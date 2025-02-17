from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class KakaoProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    kakao_id = models.CharField(max_length=100, unique=True)
    nickname = models.CharField(max_length=100, null=True)
    profile_image = models.URLField(null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Kakao Profile"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='projects/')
    created_at = models.DateTimeField(auto_now_add=True)

class NewsPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
