from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={
                'user_profile_image': 1,  # 기본 프로필 이미지 ID 설정
                'is_active': 1  # 기본 활성 상태 설정
            }
        )
