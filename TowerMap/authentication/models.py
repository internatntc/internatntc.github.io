from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Meta:
        # Add this to prevent reverse accessor clashes
        swappable = 'AUTH_USER_MODEL'