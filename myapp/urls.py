from django.urls import path
from . import views

app_name = 'myapp'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.kakao_login, name='kakao_login'),
    path('login/callback/', views.kakao_callback, name='kakao_callback'),
    path('logout/', views.logout, name='logout'),
    path('map/', views.map_view, name='map'),
    path('send-message/', views.send_kakao_message, name='send_message'),
    path('friends/', views.get_friends_list, name='friends_list'),
    path('payment/', views.kakao_pay, name='kakao_pay'),
]
