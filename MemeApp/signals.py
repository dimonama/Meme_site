from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        from .models import UserProfile
        UserProfile.objects.create(user=instance)

def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()

# Підключаємо сигнали
post_save.connect(create_user_profile, sender=User)
post_save.connect(save_user_profile, sender=User)