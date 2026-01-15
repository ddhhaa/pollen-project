from django.urls import path
from .views import home, register, login_view, logout_view, profile
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', login_view, name='login'),
    path("register/", register, name="register"),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('home/', login_required(home, login_url='/login/'), name='home'),
    path('profile/', profile, name='profile'),
]
