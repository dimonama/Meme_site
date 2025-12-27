from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.context_processors import request
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from .models import Meme, UserProfile
from .forms import CustomUserCreationForm, MemeUploadForm, UserProfileForm
from django.core.paginator import Paginator


# Головні сторінки
class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'MemeSite - Головна',
            'welcome_message': 'Ласкаво просимо на MemeSite!',
            'latest_memes': Meme.objects.all().order_by('-uploaded_at')[:6]
        })
        return context


class RegisterView(View):
    def get(self, request, *args, **kwargs):
        form = CustomUserCreationForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f'Вітаємо, {user.username}! Реєстрація успішна!')
            return redirect('MemeApp:home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
        return render(request, 'register.html', {'form': form})


class LoginView(View):
    def get(self, request):
        next_url = request.GET.get('next', '')
        return render(request, 'login.html', {'next': next_url})

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Вітаємо, {username}!')

            # Перенаправление на сохраненный URL или на главную
            next_url = request.POST.get('next', '')
            if next_url:
                return redirect(next_url)
            return redirect('MemeApp:home')
        else:
            messages.error(request, 'Невірне ім\'я користувача або пароль')

        next_url = request.POST.get('next', '')
        return render(request, 'login.html', {'next': next_url})


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, 'Ви вийшли з акаунту')
        return redirect('MemeApp:home')


class EditProfileView(LoginRequiredMixin, View):
    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        return render(request, 'Redact.html', {'user_profile': profile})

    def post(self, request):
        profile = UserProfile.objects.get(user=request.user)
        profile.avatar_emoji = request.POST['avatar_emoji']
        profile.save()
        messages.success(request, 'Аватар успішно оновлено!')
        return redirect('MemeApp:profile')


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        days_with_us = (timezone.now() - user.date_joined).days or 1

        user_memes = Meme.objects.filter(uploaded_by=user).order_by('-uploaded_at')
        created_memes_count = user_memes.count()
        total_likes = sum(meme.total_likes() for meme in user_memes)
        profile = UserProfile.objects.get(user=user)

        context = {
            'created_memes_count': created_memes_count,
            'total_likes': total_likes,
            'days_with_us': days_with_us,
            'memes': user_memes,
            'user_profile': profile
        }
        return render(request, 'profile.html', context)


class GalleryView(ListView):
    model = Meme
    template_name = 'gallery.html'
    context_object_name = 'meme_list'
    paginate_by = 14

    def get_queryset(self):
        queryset = Meme.objects.all().order_by('-uploaded_at')

        meme_type = self.request.GET.get('type')
        if meme_type in ['image', 'video']:
            queryset = queryset.filter(meme_type=meme_type)

        sort_by = self.request.GET.get('sort', 'newest')
        if sort_by == 'popular':
            queryset = queryset.annotate(like_count=Count('likes')).order_by('-like_count', '-uploaded_at')
        elif sort_by == 'views':
            queryset = queryset.order_by('-views', '-uploaded_at')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-uploaded_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'current_filter': self.request.GET.get('type'),
            'current_sort': self.request.GET.get('sort', 'newest'),
            'is_paginated': context['page_obj'].has_other_pages()
        })
        return context


class UploadMemeView(LoginRequiredMixin, View):
    login_url = 'MemeApp:login'
    redirect_field_name = 'next'

    def get(self, request):
        form = MemeUploadForm()
        return render(request, 'upload.html', {'form': form})

    def post(self, request):
        form = MemeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            meme = form.save(commit=False)
            meme.uploaded_by = request.user
            meme.save()
            messages.success(request, 'Мем успішно завантажено!')
            return redirect('MemeApp:gallery')
        else:
            messages.error(request, 'Будь ласка, виправте помилки нижче.')
        return render(request, 'upload.html', {'form': form})


class MemeDetailView(DetailView):
    model = Meme
    template_name = 'meme_detail.html'
    context_object_name = 'meme'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not request.user.is_authenticated or request.user != self.object.uploaded_by:
            self.object.views += 1
            self.object.save(update_fields=['views'])

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meme = self.get_object()

        context.update({
            'related_memes': Meme.objects.filter(
                meme_type=meme.meme_type
            ).exclude(id=meme.id).order_by('-uploaded_at')[:6]
        })
        return context


class LikeMemeView(LoginRequiredMixin, View):
    def post(self, request, meme_id):
        print(f"=== LIKE VIEW DEBUG ===")
        print(f"User: {request.user}")
        print(f"User authenticated: {request.user.is_authenticated}")
        print(f"Meme ID: {meme_id}")
        print(f"Request headers: {dict(request.headers)}")

        try:
            meme = get_object_or_404(Meme, id=meme_id)
            print(f"Meme found: {meme.title}")

            if request.user in meme.likes.all():
                meme.likes.remove(request.user)
                liked = False
                print(f"Like REMOVED for user {request.user}")
            else:
                meme.likes.add(request.user)
                liked = True
                print(f"Like ADDED for user {request.user}")

            # Получаем обновленное количество лайков
            total = meme.total_likes()
            print(f"Total likes after: {total}")

            return JsonResponse({
                'liked': liked,
                'total_likes': total,
                'success': True
            })

        except Exception as e:
            print(f"ERROR in LikeMemeView: {str(e)}")
            import traceback
            traceback.print_exc()

            return JsonResponse({
                'error': str(e),
                'success': False
            }, status=500)

class DeleteMemeView(LoginRequiredMixin, View):
    def post(self, request, meme_id):
        meme = get_object_or_404(Meme, id=meme_id)

        if meme.uploaded_by != request.user:
            return JsonResponse({'error': 'Недостатньо прав'}, status=403)

        meme_title = meme.title
        meme.delete()

        return JsonResponse({'success': True})