import torch
from torch.utils.data import DataLoader

from langchain import LLMChain
from langchain_openai import ChatOpenAI
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.memory import ConversationBufferMemory

import os
import numpy as np
import re
import json

from models.a_llmrec_model import A_llmrec_model
from pre_train.sasrec.utils import data_partition,SeqDataset_Inference

# Load environment variables from .env file
load_dotenv()

# Load API keys and other configurations from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")

# Set OpenAI API key in environment
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


class Chat_bot:
    def __init__(self,args,user_id):
        self.args = args
        self.device = args.device
        self.user_id =user_id
        self.model = "gpt-4o-mini"
        self.rank = 0
        self.model_load()
        self.find_user()

        # input_prompt_template = """
        #     역할 :
        #     - 사용자의 입력을 확인하는 역할로 요청 분석을 해야함 
        #     - 요청이 추천과 관련이 있는경우에는 미사여구를 붙이지않고 영어로 요청사항 요약 및 정리만 응답.
        #     - 요청이 추천과 관련이 없는 경우에는 대화형으로 응답.
        
        #     사용자 요청 분석:
        #     - 사용자의 요청이 상품 추천에 해당하는지 판단.
        #     - 요청이 추천과 관련이 없을 경우, 주제에 맞는 응답을 생성.
        #     - 간단한 인사나 감사에는 자연스러운 대화형 응답 생성.

        #     응답 생성 기준:
        #     - 요청이 추천과 관련 없을 경우: 한국어로 "다시 자세하게 질문해주세요" 또는 상황에 맞는 적절한 응답.
        #     - 요청이 추천과 관련 있는 경우: 영어로 다음 모델에게 전달해줄 요청을 요약 및 정리,출력에 "메롱" 추가.

        #     예시 응답:
        #     - 관련 없는 요청: "주제에서 벗어났습니다. 다시 자세하게 질문해주세요."
        #     - 감사/인사 응답: "감사합니다! 도움이 되어 기쁩니다."

        # """
        # input_prompt = PromptTemplate(input_variables=["input_text"], template=input_prompt_template)

        system_template = SystemMessagePromptTemplate.from_template(
            """
            사용자 요청: {input_text}
                beauty 관련 상품 추천 챗봇 시스템의 입력을 담당하고 있습니다. 
                경우에 따라 대답 방식이 다릅니다.
                사용자의 요청을 분석하여 Beauty 관련 상품 추천에 관한 내용인지 판별합니다. 
                Beauty 상품 추천에 관한 내용이면 다음 모델에게 전달해주는 역할입니다.
                예시 :"손이 건조한데 좋은 핸드크림있을까?" 
                아닌 경우에는 사용자에게 직접 응답을 하는 역할입니다.

                사용자의 요청이 Beauty 상품 추천에 관한 내용인 경우의 응답 방식:
                - 영어로 응답합니다.
                - 사용자의 요청을 요약하여 다음 머신에게 추천이 필요한 단어만 전달해주는 역할로 사용자는 보지못합니다.
                - response 내용만 응답합니다.
                - 'recommendation' 이란 단어는 필요하지않습니다.
                - 말끝에 "메롱"을 한국어로 붙입니다.
                - 최대한 간결하게 응답
                - 예시"skincare : Facial cleansers, moisturizers, serums 메롱" ,"footcream for dry skin 메롱"

                **다른 카테고리 상품 추천 요청일 경우:**
                - "Beauty 관련 상품 추천 시스템입니다. 다시 질문해주세요"라고 한국어로 응답합니다.

                **Beauty 상품 추천과 관계없는 요청일 경우:**
                - 한국어로 응답합니다.
                - 간단한 일상 대화나 인사는 받아줍니다.
                - 이순신 관련 질문,음식에 대한 평가 등 Beauty관련 상품과 무관한 경우에는 "부적절한 질문입니다. 다시 질문해주세요"라고 응답합니다.

            맥락: {chat_history}
            """
            )

        human_template = HumanMessagePromptTemplate.from_template(
            "사용자 요청: {input_text}\n\n"
            "요청 분석: 요청이 Beauty 제품 추천과 관련된지 판단합니다.\n"
            "Beauty 추천이 아닌 경우 챗봇으로서 직접 적절하게 응답합니다:\n"
            "- Beauty 제품 추천 이외의 간단한 일상 대화는 응대합니다.\n"
            "- Beauty와 무관한 주제(예: 이순신 관련 질문)에는 '부적절한 질문입니다. 다시 질문해주세요'라고 응답합니다.\n"
            "- 다른 카테고리의 상품 추천은 '뷰티관련 상품 추천 시스템입니다. 다시 질문해주세요'라고 응답합니다."
        )

        input_prompt = ChatPromptTemplate.from_messages([system_template, human_template])


        # output_prompt_template = """    
        # 한국어로 설명합니다.
        # 추천 결과: {input_text}
        # 추천된 아이템을 바탕으로 요구사항을 수용하여 사용자가 이해하기 쉽게 상품을 추천해줍니다.
        # history 
        # 추천 결과에서만 상품 추천을 해줍니다.
        # 추천할 것이 여러개 있으면 여러개 추천해줍니다.
        # 3~4개 정도 추천을 하고 상품이 부족하면 추천을 적게 해도 괜찬습니다.
        # 상품명은 번역하지 않습니다.
        # 적절한 추천상품이 없다면 추천할 상품이 없다고 말하거나 다시 질문을 해달라고 요청합니다.
        # """

        # output_system_template = SystemMessagePromptTemplate.from_template(

        #     """
        #     한국어로 설명합니다.
        #     추천된 아이템을 바탕으로 사용자가 이해하기 쉽게 상품을 추천해줍니다.
        #     현재 사용자의 요청과 추천 히스토리를 반영하여 최적의 상품을 제안합니다.
        #     추천 모델이 제공한 후보 중에서만 추천을 진행합니다.
        #     추천할 것이 없으면 "죄송합니다 요구사항에 맞는 상품이 없습니다." 라고 대답합니다.

        #     추천 후보: {input_text}  
        #     사용자 요청 맥락: {chat_history}  

        #     추천 결과:
        #     """

        # )

        # output_human_template = HumanMessagePromptTemplate.from_template(
        #     "추천 모델의 답: {input_text}\n\n"
        #     "추천 내용 분석\n"
        # )

        # output_prompt = ChatPromptTemplate.from_messages([output_system_template, output_human_template])

        output_prompt_template = """    
                한국어로 설명합니다.
                
                추천 결과: {input_text}
                
                model's recommendation 에서 사용자의 요구에 부합하는 상품들을 추천해줍니다.
                만약 수가 부족하다면 candidate 50에서 추가로 추천해줍니다.
                총 추천 개수는 반드시 5개로 유지합니다.
                상품명은 번역하지 않습니다.
                사용자의 요구에 적절한 추천 상품이 없다면 "추천할 상품이 없습니다."라고 응답합니다.

                출력 방식은 다음과 같습니다:
                
        
                **JSON 형식 응답** (개발자에게 전달될 출력):
                
                예시:
                (output:
                        ["요청에 따른 추천 목록입니다.
                        
                            1. 추천 상품명 : 상품에 대한 설명
                            2. 추천 상품명 : 상품에 대한 설명
                            3. 추천 상품명 : 상품에 대한 설명
                            4. 추천 상품명 : 상품에 대한 설명
                            5. 추천 상품명 : 상품에 대한 설명

                        위의 상품 중 마음에 드는 상품을 골라보세요."]
            
                        "products": [
                            "상품명1",
                            "상품명2",
                            "상품명3",
                            "상품명4",
                            "상품명5"
                        ]
                )
                
                다른 미사여구는 붙이지 않고 json 값만 응답합니다.
                """

        output_prompt = ChatPromptTemplate.from_messages([output_prompt_template])


        llm_input = ChatOpenAI(
            model_name=self.model,
            temperature=0,
            max_tokens=200
        )

        llm_output = ChatOpenAI(
            model_name=self.model,
            temperature=0,
            max_tokens=500
        )

        self.memory = ConversationBufferMemory(
            memory_key='chat_history',  
            return_messages=True       
        )

        self.llm_input_chain = LLMChain(llm=llm_input, memory=self.memory, prompt=input_prompt)
        self.llm_output_chain = LLMChain(llm=llm_output, memory=self.memory, prompt=output_prompt)
        
    def model_load(self):
        a_llmrec = A_llmrec_model(self.args).to(self.device)
        a_llmrec.load_model(self.args, phase1_epoch=20, phase2_epoch=30)
        self.a_llmrec = a_llmrec
        self.a_llmrec.eval()


    def find_user(self):

        dataset = data_partition(self.args.rec_pre_trained_data, path=f'./data/amazon/{self.args.rec_pre_trained_data}.txt')
        [user_train, user_valid, user_test, usernum, itemnum] = dataset
        print('user num:', usernum, 'item num:', itemnum)

        users = range(1, usernum + 1)
        user_list = []
        for u in users:
            if len(user_train[u]) < 1 or len(user_test[u]) < 1: continue
            user_list.append(u)


        inference_data_set = SeqDataset_Inference(user_train, user_valid, user_test, user_list, itemnum, self.args.maxlen)
        inference_data_loader = DataLoader(inference_data_set, batch_size = 1, pin_memory=True)

        for _, data in enumerate(inference_data_loader):
            u, seq, pos, neg = data
            self.u_np = u.numpy()
            if self.user_id in self.u_np:
                self.seq_np, self.pos_np, self.neg_np = seq.numpy(), pos.numpy(), neg.numpy()

                print(f"Found user {self.u_np} with seq: {self.seq_np}, pos: {self.pos_np}, neg: {self.neg_np}")
                break
        else:
            seq_length = 20
            self.seq_np = np.zeros((1, seq_length), dtype=np.int64)
            self.pos_np = np.zeros(1, dtype=np.int64)
            self.neg_np = np.zeros((1, 1), dtype=np.int64)
            print(f"User {self.user_id} not found. Initialized with seq: {self.seq_np}, pos: {self.pos_np}, neg: {self.neg_np}")


    def handle_request(self, user_request):
        transformed_request = self.llm_input_chain.predict(input_text=user_request)

        if '메롱' in transformed_request:

            cleaned_request = transformed_request.replace("메롱", "").strip()

            recommendation = self.generate_recommendation(cleaned_request)

            response = self.llm_output_chain.predict(input_text=recommendation)

            answer = self.make_json(response)
            # return response,recommendation
            # return response
            print(response,recommendation)
            return answer
        else:

            return transformed_request
    
    def generate_recommendation(self, transformed_request):

        additional_info = transformed_request

        # LLM에 전달할 입력 프롬프트 생성
        recommendation_prompt = (
            f"사용자의 요청은 '{additional_info}'입니다."
        )


        with torch.no_grad():
            result = self.a_llmrec.generate2([self.u_np, self.seq_np, self.pos_np, self.neg_np, self.rank],additional_info)
            # result = self.a_llmrec([self.u_np, self.seq_np, self.pos_np, self.neg_np, self.rank],mode = 'generate')
        recommendation_text = f"추천된 아이템: {result}"
        # print(self.memory.chat_memory.messages)
        return recommendation_prompt + "그리고 그리고 그리고 " + recommendation_text
        # return recommendation_prompt 

    def make_json(self,response):
        # 코드 블록 및 백틱 제거
        cleaned_response = re.sub(r'^```json\s*', '', response)
        cleaned_response = re.sub(r'^```', '', cleaned_response)
        cleaned_response = re.sub(r'```$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        # JSON 파싱
        try:
            data = json.loads(cleaned_response)
            print(data)
            return data
        except json.JSONDecodeError as e:
            print("JSON 파싱 오류:", e)
            return cleaned_response