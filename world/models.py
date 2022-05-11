from django.contrib.auth.models import AbstractUser
from django.db import models

class Country(models.Model):
    country_name = models.CharField(max_length=255)
    #been = models.BooleanField(default=False)
    #traveler = models.ManyToManyField(User, related_name="countries_been")

class User(AbstractUser):
    following = models.ManyToManyField("User", related_name="followers")
    been = models.ManyToManyField(Country, related_name="countries_been")

class Post(models.Model):
    poster = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    body = models.TextField(max_length=195)
    timestamp = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name="liked")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="flutters")

    class Meta:
        ordering = ['-timestamp']

    def serialize(self):
        return {
            "id": self.id,
            "country": self.country.country_name,
            "poster": self.poster.username,
            "body": self.body,
            "timestamp": self.timestamp.strftime("%b %d %Y, %I:%M %p"),
            "likes": self.likes.count(),
            "liked_by": [like.username for like in self.likes.all()]
        }
