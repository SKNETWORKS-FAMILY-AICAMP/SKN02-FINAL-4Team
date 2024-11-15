# chatbot/views.py

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
from django.utils import timezone
from .models import WebChatList, Question, Answer
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
import requests
from django.views.decorators.http import require_POST
from myapp.models import Profile, MetaData  # Profile과 MetaData 모델 임포트
from django.db.models import Q

MODEL_SERVER_URL = settings.MODEL_SERVER_URL
generate_endpoint = f"{MODEL_SERVER_URL}/generate"

@csrf_exempt
def chatbot_response(request):
    data = json.loads(request.body)
    user_message = data.get("message")
    chat_id = data.get("chat_id")

    if request.user.is_authenticated:
        user_profile = request.user.profile
        user_id = request.user.id
    else:
        user_profile = None  # 비로그인 사용자는 프로필이 없음
        user_id = 0  # 비로그인 사용자는 user_id를 0으로 설정

    # 기존 채팅 가져오기 또는 새로운 채팅 생성
    if chat_id is not None and request.user.is_authenticated:
        chat = WebChatList.objects.filter(chat_id=chat_id, user=user_profile).first()
        if not chat:
            return JsonResponse({"error": "해당 채팅을 찾을 수 없습니다."})
    elif request.user.is_authenticated:
        # 로그인된 사용자의 경우 새로운 채팅 생성
        chat = WebChatList.objects.create(
            user=user_profile,
            chat_last_timestamp=timezone.now(),
            chat_status=1
        )
    else:
        chat = None  # 비로그인 사용자는 채팅 객체를 생성하지 않음

    # 모델 서버에 보낼 페이로드 준비
    payload = {
        "user_id": user_id,
        "prompt": user_message
    }

    # 모델 서버의 /generate 엔드포인트로 POST 요청 보내기
    try:
        response = requests.post(generate_endpoint, json=payload)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

        result = response.json()

        # 모델의 응답 추출
        generated_text = result.get("generated_text", {})

        chatbot_message = ""
        products_list = []

        if isinstance(generated_text, dict):
            output = generated_text.get("output", [])
            products_list = generated_text.get("products", [])
            if isinstance(output, list) and len(output) >= 1:
                chatbot_message = output[0]  # 첫 번째 요소는 챗봇 메시지
            else:
                chatbot_message = str(generated_text)
        elif isinstance(generated_text, str):
            chatbot_message = generated_text
        else:
            chatbot_message = ""

        # 제품 목록을 문자열로 변환하여 저장
        product_data = []
        if products_list:
            if request.user.is_authenticated:
                # 로그인된 사용자의 경우 프로필에 저장
                user_profile.user_products = ','.join(products_list)
                user_profile.save()
            else:
                # 비로그인 사용자의 경우 세션에 저장
                request.session['user_products'] = ','.join(products_list)

            # 제품 정보를 가져와서 응답에 포함
            product_names = [name.strip() for name in products_list]
            queries = Q()
            for product_name in product_names:
                queries |= Q(summarized_description__icontains=product_name)
                queries |= Q(summarized_title__icontains=product_name)
                queries |= Q(title__icontains=product_name)

            products = MetaData.objects.using('rawdb').filter(queries)
            # 필요한 필드만 선택하여 JSON으로 반환
            for product in products:
                product_data.append({
                    'images': product.images,
                    'title': product.title,
                    'summarized_title': product.summarized_title,
                })

        if request.user.is_authenticated:
            # 로그인된 사용자의 경우 질문과 답변을 저장
            question = Question.objects.create(
                user=user_profile,
                chat=chat,
                question_content=user_message,
                question_timestamp=timezone.now()
            )

            # 챗봇의 답변 저장
            Answer.objects.create(
                user=user_profile,
                chat=chat,
                question=question,
                answer_content=chatbot_message,
                answer_timestamp=timezone.now()
            )

            # 채팅의 마지막 활동 시간 업데이트
            chat.chat_last_timestamp = timezone.now()
            chat.save()

            # JSON 응답에 products 데이터 포함
            return JsonResponse({
                "response": chatbot_message,
                "chat_id": chat.chat_id,
                "products": product_data
            })
        else:
            # 비로그인 사용자의 경우 응답과 products만 반환
            return JsonResponse({"response": chatbot_message, "products": product_data})

    except requests.exceptions.RequestException as e:
        # 모델 서버에서 응답을 받지 못한 경우 오류 처리
        chatbot_message = "죄송합니다. 현재 요청을 처리할 수 없습니다. 다시 시도해 주세요."

        # 로그에 오류 내용 출력 (디버깅용)
        print("모델 서버 요청 오류:", str(e))

        if request.user.is_authenticated:
            # 로그인된 사용자의 경우 질문과 답변을 저장
            question = Question.objects.create(
                user=user_profile,
                chat=chat,
                question_content=user_message,
                question_timestamp=timezone.now()
            )

            # 챗봇의 답변 저장
            Answer.objects.create(
                user=user_profile,
                chat=chat,
                question=question,
                answer_content=chatbot_message,
                answer_timestamp=timezone.now()
            )

            # 채팅의 마지막 활동 시간 업데이트
            chat.chat_last_timestamp = timezone.now()
            chat.save()

            return JsonResponse({"response": chatbot_message, "chat_id": chat.chat_id})
        else:
            # 비로그인 사용자의 경우 응답만 반환
            return JsonResponse({"response": chatbot_message})

@login_required
def chat_list(request):
    print("chat_list view triggered")  # Basic print to confirm the view is called
    chats = WebChatList.objects.filter(user_id=request.user.id, chat_status=1).order_by('-chat_last_timestamp')
    if chats.exists():
        print("Chats found:", list(chats))
    else:
        print("No chats found for this user.")

    return render(request, 'chat_list.html', {'chats': chats})

@login_required
def chat_detail(request, chat_id):
    chat = WebChatList.objects.get(chat_id=chat_id, user_id=request.user.id)
    questions = Question.objects.filter(chat_id=chat_id).order_by('question_timestamp')
    answers = Answer.objects.filter(chat_id=chat_id).order_by('answer_timestamp')
    conversation = zip(questions, answers)
    html_content = render_to_string('chat_detail.html', {'chat': chat, 'conversation': conversation})
    return HttpResponse(html_content)

@login_required
def chatbot_view(request):
    chats = WebChatList.objects.filter(user_id=request.user.id, chat_status=1).order_by('-chat_last_timestamp')
    return render(request, 'chatbot.html', {'chats': chats})

@login_required
def new_chat(request):
    if request.method == "POST":
        chat = WebChatList.objects.create(
            user=request.user.profile,
            chat_last_timestamp=timezone.now(),
            chat_status=1
        )
        return JsonResponse({"chat_id": chat.chat_id})

@login_required
@require_POST
def delete_chat(request, chat_id):
    """
    Soft deletes a chat by setting chat_status to 0.
    """
    chat = get_object_or_404(WebChatList, chat_id=chat_id, user=request.user.profile)
    chat.chat_status = 0  # Set status to indicate deletion
    chat.save()  # Save the changes to the database
    return JsonResponse({"success": True, "message": "Chat deleted successfully."})

