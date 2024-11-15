import os
import gzip
import json
import pickle
from tqdm import tqdm
from collections import defaultdict
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv  # 추가
import time  # time 모듈 추가

# .env 파일에서 환경 변수 불러오기
load_dotenv()

# API 키를 환경 변수에서 가져오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY)

def parse(path):
    g = gzip.open(path, 'rb')
    for l in tqdm(g, desc="Parsing JSON Lines"):  # tqdm 추가
        yield json.loads(l)

def preprocess(fname):
    countU = defaultdict(lambda: 0)
    countP = defaultdict(lambda: 0)
    line = 0

    file_path = f'../../data/amazon/{fname}.jsonl.gz'

    # 시간 필터링을 위한 날짜 범위 설정
    start_date = datetime(2013, 1, 1)
    end_date = datetime(2023, 8, 31, 23, 59, 59)

    # 사용자와 아이템의 상호작용 수를 카운팅
    print("Counting interactions between users and items...")
    for l in parse(file_path):
        line += 1
        asin = l.get('asin')
        if asin is None:
            asin = l.get('parent_asin')
            if asin is None:
                print(f"Line {line}: 리뷰 데이터에서 'asin' 또는 'parent_asin'을 찾을 수 없습니다. 건너뜁니다.")
                continue
        rev = l['user_id']
        time = l['timestamp'] // 1000

        # 시간 필터 적용
        review_date = datetime.utcfromtimestamp(time)
        if review_date < start_date or review_date > end_date:
            continue

        countU[rev] += 1
        countP[asin] += 1

    usermap = dict()
    usernum = 0
    itemmap = dict()
    itemnum = 0
    User = dict()
    review_dict = {}
    name_dict = {'title': {}, 'description': {}}

    # 메타데이터 로드
    meta_dict = load_meta_data(fname)

    # 데이터 처리 루프
    line = 0  # 라인 카운터 초기화
    print("Processing data and filtering by time...")
    for l in tqdm(parse(file_path), desc="Processing Data"):  # tqdm 추가
        line += 1
        asin = l.get('asin')
        if asin is None:
            asin = l.get('parent_asin')
            if asin is None:
                continue
        rev = l['user_id']
        time = l['timestamp'] // 1000

        # 시간 필터 적용
        review_date = datetime.utcfromtimestamp(time)
        if review_date < start_date or review_date > end_date:
            continue

        threshold = 4

        if countU[rev] < threshold or countP[asin] < threshold:
            continue

        if rev in usermap:
            userid = usermap[rev]
        else:
            usernum += 1
            userid = usernum
            usermap[rev] = userid
            User[userid] = []

        if asin in itemmap:
            itemid = itemmap[asin]
        else:
            itemnum += 1
            itemid = itemnum
            itemmap[asin] = itemid
        User[userid].append([time, itemid])

        if itemmap[asin] in review_dict:
            try:
                review_dict[itemmap[asin]]['review'][usermap[rev]] = l['text']
            except KeyError:
                pass
            try:
                review_dict[itemmap[asin]]['summary'][usermap[rev]] = l['title']
            except KeyError:
                pass
        else:
            review_dict[itemmap[asin]] = {'review': {}, 'summary': {}}
            try:
                review_dict[itemmap[asin]]['review'][usermap[rev]] = l['text']
            except KeyError:
                pass
            try:
                review_dict[itemmap[asin]]['summary'][usermap[rev]] = l['title']
            except KeyError:
                pass

        try:
            # 설명 처리
            if 'description' in meta_dict[asin] and len(meta_dict[asin]['description']) == 0:
                name_dict['description'][itemmap[asin]] = 'Empty description'
            else:
                name_dict['description'][itemmap[asin]] = meta_dict[asin].get('description', ['Empty description'])[0]

            # 원본 타이틀 가져오기
            original_title = meta_dict[asin].get('title', 'No title')

            # 원본 타이틀을 name_dict에 할당
            name_dict['title'][itemmap[asin]] = original_title

        except KeyError:
            pass

    # 타이틀과 디스크립션 요약 및 매핑 저장 함수 호출
    summarize_and_save_titles_and_descriptions(name_dict, fname)

    with open(f'../../data/amazon/{fname}_text_name_dict.json.gz', 'wb') as tf:
        pickle.dump(name_dict, tf)

    for userid in User.keys():
        User[userid].sort(key=lambda x: x[0])

    print(usernum, itemnum)

    with open(f'../../data/amazon/{fname}.txt', 'w') as f:
        for user in User.keys():
            for i in User[user]:
                f.write('%d %d\n' % (user, i[1]))
    # 파일을 닫을 필요 없음 (with 블록 사용)

# 추가된 함수들

def load_meta_data(fname):
    """메타 데이터를 로드하고 asin을 키로 하는 딕셔너리를 반환합니다."""
    meta_dict = {}
    print("Loading metadata...")
    with open(f'../../data/amazon/meta_{fname}.jsonl', 'r') as f:
        for line in tqdm(f, desc="Loading Metadata"):  # tqdm 추가
            l = json.loads(line.strip())
            asin = l.get('asin')
            if asin is None:
                asin = l.get('parent_asin')
                if asin is None:
                    print("메타 데이터에서 'asin' 또는 'parent_asin'을 찾을 수 없습니다. 건너뜁니다.")
                    continue
            meta_dict[asin] = l
    return meta_dict

def summarize_and_save_titles_and_descriptions(name_dict, fname):
    """타이틀과 디스크립션을 각각 요약하고, 각각의 매핑을 파일에 저장합니다."""
    title_cache = {}
    title_mapping = {}
    description_cache = {}
    description_mapping = {}

    # 타이틀 요약
    for itemid, original_title in tqdm(name_dict['title'].items(), desc="Summarizing Titles"):  # tqdm 추가
        if original_title in title_cache:
            summarized_title = title_cache[original_title]
        else:
            try:
                summarized_title = summarize_title(original_title)
                title_cache[original_title] = summarized_title
            except Exception as e:
                print(f"타이틀 요약 중 오류 발생: {e}")
                summarized_title = original_title  # 오류 시 원본 타이틀 사용

        name_dict['title'][itemid] = summarized_title
        title_mapping[original_title] = summarized_title

    # 디스크립션 요약
    for itemid, original_description in tqdm(name_dict['description'].items(), desc="Summarizing Descriptions"):  # tqdm 추가
        if original_description in description_cache:
            summarized_description = description_cache[original_description]
        else:
            try:
                summarized_description = summarize_description(original_description)
                description_cache[original_description] = summarized_description
            except Exception as e:
                print(f"디스크립션 요약 중 오류 발생: {e}")
                summarized_description = original_description  # 오류 시 원본 디스크립션 사용

        name_dict['description'][itemid] = summarized_description
        description_mapping[original_description] = summarized_description

    # 타이틀 매핑 저장
    with open(f'../../data/amazon/{fname}_title_sum_match.jsonl', 'w', encoding='utf-8') as f:
        for original_title, summarized_title in title_mapping.items():
            json_line = json.dumps({'original_title': original_title, 'summarized_title': summarized_title}, ensure_ascii=False)
            f.write(json_line + '\n')
    
    # 디스크립션 매핑 저장
    with open(f'../../data/amazon/{fname}_description_sum_match.jsonl', 'w', encoding='utf-8') as f:
        for original_description, summarized_description in description_mapping.items():
            json_line = json.dumps({'original_description': original_description, 'summarized_description': summarized_description}, ensure_ascii=False)
            f.write(json_line + '\n')


# 타이틀 요약 함수
def summarize_title(title, model="gpt-4o-mini"):
    """
    GPT API를 사용하여 타이틀을 요약하는 함수.

    Args:
        title (str): 요약할 타이틀
        model (str): 사용할 GPT 모델

    Returns:
        str: 요약된 타이틀
    """
    try:
        # OpenAI API 호출하여 타이틀 요약
        chat_completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an extremely efficient title summarizer. Your task is to summarize the provided title by identifying and focusing on the important product name. Avoid unnecessary details and focus on the key product name."
                },
                {
                    "role": "user", 
                    "content": f"Here is the title: {title}. Summarize it by focusing on the key product name and essential features, avoiding unnecessary details."
                }
            ],
            max_tokens=30,
            temperature=0.7,
        )
        time.sleep(1)  # 딜레이 추가
        summary = chat_completion.choices[0].message.content.strip()
        return summary

    except Exception as e:
        print(f"Error during GPT API call: {e}")
        return title  # 에러 발생 시 원래 타이틀 반환

# 디스크립션 요약 함수
def summarize_description(description, model="gpt-4o-mini"):
    """
    GPT API를 사용하여 디스크립션을 요약하는 함수.

    Args:
        description (str): 요약할 디스크립션
        model (str): 사용할 GPT 모델

    Returns:
        str: 요약된 디스크립션
    """
    try:
        # OpenAI API 호출하여 디스크립션 요약
        chat_completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an efficient description summarizer. Your task is to summarize the product description by focusing on the most important features and aspects. Remove any unnecessary details and provide a concise version of the description."
                },
                {
                    "role": "user", 
                    "content": f"Here is the description: {description}. We condense the given Amazon product metadata into a concise, relevant description that focuses on the information that matters most to the customers and eliminates unnecessary details. Given the title information and other descriptions on the product, extract and summarize your product's key features and benefits."
                }
            ],
            max_tokens=50,
            temperature=0.7,
        )
        time.sleep(1)  # 딜레이 추가
        summary = chat_completion.choices[0].message.content.strip()
        return summary

    except Exception as e:
        print(f"Error during GPT API call: {e}")
        return description  # 에러 발생 시 원래 디스크립션 반환

# 테스트 예시
if __name__ == "__main__":
    preprocess('your_filename')  # 'your_filename'을 실제 파일명으로 변경하세요
