from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Users(models.Model):
    username = models.CharField(max_length=30)
    email = models.EmailField(max_length=30)
    password = models.CharField(max_length=30)
    firstName = models.CharField(max_length=30)
    lastName = models.CharField(max_length=30)
    attendance = models.IntegerField(max_length=1)



class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# class UserProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     photo = models.ImageField(upload_to='profile_photos')

#     def __str__(self):
#         return self.user.username