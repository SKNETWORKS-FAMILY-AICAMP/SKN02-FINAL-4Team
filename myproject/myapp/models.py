from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class MetaData(models.Model):
    meta_id = models.AutoField(primary_key=True)
    main_category = models.CharField(max_length=50)
    title = models.CharField(max_length=50)
    average_rating = models.FloatField()
    rating_number = models.IntegerField()
    features = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    price = models.CharField(max_length=50)
    images = models.CharField(max_length=255)
    videos = models.CharField(max_length=255)
    store = models.CharField(max_length=50)
    categories = models.CharField(max_length=50)
    details = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    deleted_time = models.DateTimeField()
    summarized_description = models.CharField(max_length=1500, null=True, blank=True)
    summarized_title = models.CharField(max_length=500, null=True, blank=True)
    mapped_item_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'meta'

class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, db_column='user_id', primary_key=True
    )
    user_profile_image = models.IntegerField(default=1)
    is_active = models.IntegerField(default=1)
    user_products = models.CharField(max_length=1000, null=True, blank=True)
    user_deleted_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'profile' 

    def get_profile_image_url(self):
        # Mapping integer IDs to image filenames
        image_mapping = {
            1: 'static/images/default_profile.jpg',
            2: 'static/images/profile_potato.PNG',
            3: 'static/images/profile_sweetpotato.PNG',
            4: 'static/images/profile_broccoli.PNG',
            5: 'static/images/profile_corn.PNG',
        }
        # Return the corresponding image path or a default if not found
        return image_mapping.get(self.user_profile_image, 'static/images/default_profile.jpg')
        
@receiver(post_save, sender=User)
def sync_is_active(sender, instance, **kwargs):
    try:
        profile = Profile.objects.get(user=instance)
        profile.is_active = instance.is_active  # Synchronize `is_active` with `auth_user`
        profile.save()
    except Profile.DoesNotExist:
        # Create a new Profile if it doesn't exist
        Profile.objects.create(user=instance, is_active=instance.is_active)
