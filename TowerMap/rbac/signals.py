from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Create or update the user profile when a User instance is saved.
    """
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Ensure existing users get a profile if somehow they don't have one
        if not hasattr(instance, 'profile'):
            UserProfile.objects.create(user=instance)
        instance.profile.save()
