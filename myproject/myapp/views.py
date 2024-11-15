# myapp/views.py

from django.db.models import Q
from .models import MetaData
from chatbot.models import WebChatList  # Adjust the import as needed for your project
from django.shortcuts import render

def home(request):
    # 기본적으로 rawdb의 모든 MetaData를 가져옵니다.
    main_images = MetaData.objects.using('rawdb').all()
    chats = []

    if request.user.is_authenticated:
        # 사용자 채팅 목록 가져오기
        chats = WebChatList.objects.filter(user_id=request.user.id, chat_status=1).order_by('-chat_last_timestamp')

        # 사용자 프로필 가져오기
        user_profile = request.user.profile

        if user_profile.user_products:
            # user_products 필드를 ','로 분리하여 제품 이름 리스트 생성
            product_names = [name.strip() for name in user_profile.user_products.split(',') if name.strip()]

            if product_names:
                # 쿼리를 사용하여 제품 검색
                queries = Q()
                for product_name in product_names:
                    queries |= Q(summarized_description__icontains=product_name)
                    queries |= Q(summarized_title__icontains=product_name)
                    queries |= Q(title__icontains=product_name)

                # 제품 검색
                products = MetaData.objects.using('rawdb').filter(queries)

                if products.exists():
                    # 검색된 제품이 있으면 main_images를 업데이트
                    main_images = products
    else:
        # 비로그인 사용자의 경우 세션에서 user_products 가져오기
        user_products = request.session.get('user_products')
        if user_products:
            product_names = [name.strip() for name in user_products.split(',') if name.strip()]

            if product_names:
                # 쿼리를 사용하여 제품 검색
                queries = Q()
                for product_name in product_names:
                    queries |= Q(summarized_description__icontains=product_name)
                    queries |= Q(summarized_title__icontains=product_name)
                    queries |= Q(title__icontains=product_name)

                # 제품 검색
                products = MetaData.objects.using('rawdb').filter(queries)

                if products.exists():
                    # 검색된 제품이 있으면 main_images를 업데이트
                    main_images = products

    return render(request, 'home.html', {'main_images': main_images, 'chats': chats})

