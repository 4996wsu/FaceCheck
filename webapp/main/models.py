from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import User

# Define a model to store user information
class Users(models.Model):
    username = models.CharField(max_length=30)  # Field to store the username
    email = models.EmailField(max_length=30)  # Field to store the email address
    password = models.CharField(max_length=30)  # Field to store the password (consider using hashing for security)
    firstName = models.CharField(max_length=30)  # Field to store the first name of the user
    lastName = models.CharField(max_length=30)  # Field to store the last name of the user
    attendance = models.IntegerField(max_length=1)  # Field to store the attendance status (e.g., 0 or 1)

# Define a model to represent posts or articles
class Post(models.Model):
    title = models.CharField(max_length=100)  # Field to store the title of the post
    content = models.TextField()  # Field to store the content of the post
    date_created = models.DateTimeField(auto_now_add=True)  # Field to store the date and time of post creation

    def __str__(self):
        return self.title  # Return the title of the post as its string representation
