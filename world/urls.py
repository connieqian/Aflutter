from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("profile/<int:user_id>", views.profile, name="profile"),
    path("countries", views.countries, name="countries"),
    path("countries/<int:country_id>", views.country, name="country"),
    path("following", views.following, name="following"),
    path("post/<int:post_id>", views.update, name="update"),
    path("like/<int:post_id>", views.like, name="like"),
    path("add_countries", views.add_countries, name='add_countries'),
]