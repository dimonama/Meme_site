from django.urls import path
from . import views

app_name = 'MemeApp'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.EditProfileView.as_view(), name='edit_profile'),
    path('gallery/', views.GalleryView.as_view(), name='gallery'),
    path('upload/', views.UploadMemeView.as_view(), name='upload'),
    path('meme/<int:pk>/', views.MemeDetailView.as_view(), name='meme_detail'),
    path('meme/<int:meme_id>/like/', views.LikeMemeView.as_view(), name='like_meme'),
    path('meme/<int:meme_id>/delete/', views.DeleteMemeView.as_view(), name='delete_meme'),
]