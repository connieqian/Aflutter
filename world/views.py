from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, connection
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
import json
import folium
from datetime import datetime
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from .models import *

# Populate the Country model with countries from json file
def populate_countries():
    with open('world/static/json/countries.json', 'r') as file:
        data = json.load(file)
        for feature in data['features']:
            country_name = feature['properties']['NAME']
            new_country = Country.objects.get_or_create(country_name=country_name)[0]

populate_countries()

# Display flutters from all users in reverse chronological order
@csrf_exempt
def index(request):
    # Saves new post 
    user = request.user
    msg = ""

    if request.method == "POST":
        post = request.POST["post"]
        input_country = request.POST["country_selections"]
        if post == "" or input_country == "Select a country":
            msg = "empty"
        elif len(post) > 195:
            msg = "error"
        else:
            Post.objects.create(
                poster = user,
                body = post,
                country = Country.objects.get(country_name = input_country)
            )
            msg = "success"

    # Queries all posts
    posts = Post.objects.all()

    # Add pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    posts = page_obj.object_list

    return render(request, "world/index.html", {
        "countries": Country.objects.order_by("country_name").all(),
        "msg": msg,
        "posts": posts,
        "page_obj": page_obj
    })


# Displays the login page
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "world/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "world/login.html")


# Displays the logout page
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


# Displays the user registration page
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "world/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "world/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "world/register.html")

# Displays a list of all countries names in alphabetic order
def countries(request):
    return render(request, "world/countries.html", {
        "countries": Country.objects.order_by("country_name").all(),
        "count": Country.objects.count()
    })

# Displays flutters on a country (order: most to least liked)
def country(request, country_id):
    # Filters posts by the country id
    country = get_object_or_404(Country, pk=country_id)
    posts = Post.objects.filter(country=country).annotate(num_likes=Count('likes')).order_by("-num_likes", "-timestamp").all()
    
    # Add paginator with 10 posts per page
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    posts = page_obj.object_list

    return render(request, "world/country.html", {
        "country": country.country_name,
        "posts": posts,
        "page_obj": page_obj
    })

# Displays all posts made by travelers that the user follows
@login_required
def following(request):
    username = request.user
    posts = Post.objects.filter(poster__in=username.following.all())

    # Add paginator with 10 posts per page
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    posts = page_obj.object_list

    return render(request, "world/following.html", {
        "countries": Country.objects.order_by("country_name").all(),
        "posts": posts,
        "page_obj": page_obj
    })


# Retrives body of the post and allows user to update the body
@csrf_exempt
@login_required
def update(request, post_id):
    post = Post.objects.get(pk=post_id)
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    
    data = json.loads(request.body)
    if data.get("body") is not None:
        post.body = data["body"]
        post.save(update_fields=["body"])

    return JsonResponse({"message": "Your post was successfully updated."}, status=201)


# Allows user to like and unlike a post
@csrf_exempt
@login_required
def like(request, post_id):
    user = request.user.id

    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found."}, status=404)

    if request.method == "GET":
        return JsonResponse(post.serialize())
    elif request.method == "PUT":
        data = json.loads(request.body)
        if data["likes"]:
            post.likes.add(user)
        else:
            post.likes.remove(user)
        return HttpResponse(status=204)
    else:
        return JsonResponse({"error": "GET or PUT request required."}, status=400)


# Displays a form to add countries the user has been to and lists them
@csrf_exempt
@login_required
def add_countries(request):
    # Saves each new country added by the user 
    user = request.user
    
    if request.method == "POST":
        country_added = request.POST["country_selection"]
        if country_added in user.been.all():
            pass
        else:
            user.been.add(Country.objects.get(country_name = country_added))
        
    countries_been = user.been.all().order_by("country_name")
    countries_count = user.been.all().count()
    countries_pctg = (countries_count / Country.objects.count()) * 100

    # create and show blank map
    m = folium.Map(location=[20,0], tiles="OpenStreetMap", zoom_start=2)
    m.get_root().html.add_child(folium.Element("""
    <body style="font-family: 'Courier Prime'">
    </body>
    """))
    m.save('world/templates/world/blank_map.html')
    
    return render(request, "world/add_countries.html", {
        "countries_been": countries_been,
        "countries_been_count": countries_count,
        "countries": Country.objects.order_by("country_name").all(),
        "countries_pctg": f"{countries_pctg:.2f}%",
        "file": "world/blank_map.html"
    })

# Changes the color of a Folium map
def get_color(country_data, countries_been):
    for x in countries_been:
        if x in country_data['properties']['NAME']:
            return 'red'
    else:
        return 'white'

# Displays a user's profile page 
@csrf_exempt
def profile(request, user_id):
    user = request.user
    poster = User.objects.get(pk=user_id)
    countries_count = poster.been.all().count()
    countries_pctg = (countries_count / Country.objects.count()) * 100

    # Create and save map highlighting countries that the traveler has been to
    my_map = folium.Map(location=[35, 0], zoom_start=1.5, zoom_control=False, control_scale=False, no_touch=True, min_zoom=2)
    countries_been = list(poster.been.values_list('country_name', flat = True))
    gj = folium.GeoJson(
        data=open("world/static/json/countries.json", "r", encoding="utf-8-sig").read(),
        style_function=lambda country_data: {
            'fillColor': get_color(country_data, countries_been),
            'fillOpacity': 0.5,
            'color': 'black',
            'line_opacity': 0.5,
            'weight': 1
        })
    gj.add_to(my_map)

    my_map.get_root().html.add_child(folium.Element("""
    <body style="font-family: 'Courier Prime'">
    </body>
    """))

    my_map.save(f'world/templates/world/my_map_{user_id}.html')
    file = f'world/my_map_{user_id}.html'

    # Filter posts by the requested user
    posts = Post.objects.filter(poster=user_id)
    count = posts.count()

    # Add pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    posts = page_obj.object_list

    # Let the current user toggle whether to follow the requested user
    if request.method == "POST":
        if user.following.filter(id=poster.id).exists():
            user.following.remove(poster)
        else:
            user.following.add(poster)

    follows = poster.following.all().count() 
    followers = poster.followers.all().count()
    following = False

    if follows == "":
        follows = 0

    if followers == "":
        followers = 0

    if user.following.filter(id=poster.id).exists():
        following = True

    return render(request, "world/profile.html", {
        "user": user,
        "poster": poster,
        "posts": posts,
        "page_obj": page_obj,
        "count": count,
        "follows": follows,
        "followers": followers,
        "following": following,
        'file': file,
        "countries_been_count": countries_count,
        "countries_pctg": f"{countries_pctg:.2f}%"
    })