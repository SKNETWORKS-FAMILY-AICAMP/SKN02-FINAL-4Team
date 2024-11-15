from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from common.forms import UserForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from myapp.models import Profile
from django.utils import timezone
import requests  # 추가된 부분: 모델 서버와 통신하기 위해 requests 모듈 임포트
from django.conf import settings  # 추가된 부분: MODEL_SERVER_URL 가져오기

# 모델 서버 URL 설정
MODEL_SERVER_URL = settings.MODEL_SERVER_URL

def logout_view(request):
    user_id = request.user.id  # 로그아웃 전에 사용자 ID를 가져옵니다.
    logout(request)
    # 모델 인스턴스 종료 요청 보내기
    stop_instance_endpoint = f"{MODEL_SERVER_URL}/stop_instance"
    payload = {"user_id": user_id}
    try:
        response = requests.post(stop_instance_endpoint, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # 오류 처리 (필요에 따라 로그 또는 사용자 알림 추가 가능)
        pass
    return redirect('/')

def signup(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)  # 사용자 인증
            login(request, user)  # 로그인

            # 모델 인스턴스 시작 요청 보내기
            start_instance_endpoint = f"{MODEL_SERVER_URL}/start_instance"
            payload = {"user_id": user.id}
            try:
                response = requests.post(start_instance_endpoint, json=payload)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                # 오류 처리 (필요에 따라 로그 또는 사용자 알림 추가 가능)
                pass

            return redirect('/')
    else:
        form = UserForm()
    return render(request, 'common/signup.html', {'form': form})

def login_view(request):
    print("login_view 함수가 호출되었습니다.")  # 로그 추가
    if request.method == 'POST':
        # 로그인 폼 처리 로직
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            print(f"사용자 인증 성공: {user.username}")  # 로그 추가
            login(request, user)
            # 모델 인스턴스 시작 요청 보내기
            start_instance_endpoint = f"{MODEL_SERVER_URL}/start_instance"
            payload = {"user_id": user.id}
            try:
                response = requests.post(start_instance_endpoint, json=payload)
                response.raise_for_status()
                print(f"모델 인스턴스 시작 요청 성공: user_id={user.id}, 응답={response.json()}")  # 로그 추가
            except requests.exceptions.RequestException as e:
                print(f"모델 인스턴스 시작 중 오류 발생: {e}")  # 로그 추가
            return redirect('/')
        else:
            print("사용자 인증 실패")  # 로그 추가
            # 로그인 실패 처리
            return render(request, 'common/login.html', {'error': '아이디 또는 비밀번호가 올바르지 않습니다.'})
    else:
        print("GET 요청으로 로그인 페이지 표시")  # 로그 추가
        # 로그인 폼 렌더링
        return render(request, 'common/login.html')

@login_required
def update_profile_image(request):
    if request.method == "POST":
        data = json.loads(request.body)
        image_id = data.get("image_id")

        if image_id in [2, 3, 4, 5]:  # 허용되는 이미지 ID
            profile = Profile.objects.get(user=request.user)
            profile.user_profile_image = image_id
            profile.save()

            # 이미지 파일이 ID로 명명되어 있다고 가정
            image_url = f'/static/images/profile_{image_id}.PNG'
            return JsonResponse({"success": True, "new_image_url": image_url})

    return JsonResponse({"success": False})

@login_required
def delete_account(request):
    user = request.user

    # `auth_user` 테이블의 `is_active` 컬럼 업데이트
    user.is_active = 0
    user.save()

    # `Profile` 테이블의 `is_active` 및 `user_deleted_time` 업데이트
    try:
        profile = Profile.objects.get(user=user)
        profile.is_active = 0
        profile.user_deleted_time = timezone.now()
        profile.save()
    except Profile.DoesNotExist:
        # Profile이 존재하지 않는 경우 처리
        pass

    # 모델 인스턴스 종료 요청 보내기
    stop_instance_endpoint = f"{MODEL_SERVER_URL}/stop_instance"
    payload = {"user_id": user.id}
    try:
        response = requests.post(stop_instance_endpoint, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # 오류 처리 (필요에 따라 로그 또는 사용자 알림 추가 가능)
        pass

    # 계정 삭제 후 로그아웃
    logout(request)

    # 홈페이지 또는 종료 페이지로 리디렉션
    return redirect('myapp:home')  # 'home'을 적절한 URL 이름으로 대체하세요

@login_required
def profile(request):
    return render(request, 'common/profile.html', {'username': request.user.username})
