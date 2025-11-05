from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Meme, UserProfile


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Ім'я користувача"
            }),
        }


class MemeUploadForm(forms.ModelForm):
    class Meta:
        model = Meme
        fields = ['title', 'description', 'file']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Опиши свій мем...',
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'Назва мему...',
                'class': 'form-control'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,video/*'
            }),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov']
            ext = '.' + file.name.lower().split('.')[-1]
            if ext not in valid_extensions:
                raise forms.ValidationError(
                    "Непідтримуваний формат файлу. Дозволені: JPG, PNG, GIF, MP4, AVI, MOV"
                )

            max_size = 10 * 1024 * 1024
            if file.size > max_size:
                raise forms.ValidationError(
                    f"Файл занадто великий. Максимальний розмір: {max_size // 1024 // 1024}MB"
                )
        return file


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Розкажіть про себе...'
            }),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if avatar.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Розмір аватара не повинен перевищувати 2MB")
        return avatar