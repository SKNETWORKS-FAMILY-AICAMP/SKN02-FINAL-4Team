# common/context_processors.py
from myapp.models import Profile
from chatbot.models import WebChatList


def profile_image(request):
    if request.user.is_authenticated:
        # Ensure the profile is created if it doesn't exist
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        # Retrieve the profile image ID and map it to the image path
        profile_image_id = profile.user_profile_image
        
        image_mapping = {
            1: "images/default_profile.jpg",
            2: "images/profile_potato.PNG",
            3: "images/profile_sweetpotato.PNG",
            4: "images/profile_broccoli.PNG",
            5: "images/profile_corn.PNG"
        }
        profile_image_path = image_mapping.get(profile_image_id, "images/default_profile.jpg")
        
        return {"profile_image_path": profile_image_path}
    return {}


def current_chat(request):
    if request.user.is_authenticated:
        last_chat = WebChatList.objects.filter(user_id=request.user.id, chat_status=1).order_by('-chat_last_timestamp').first()
        return {'last_chat': last_chat}
    return {}
