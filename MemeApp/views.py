from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from .models import Meme, UserProfile
from .forms import CustomUserCreationForm, MemeUploadForm, UserProfileForm


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
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Вітаємо, {username}!')
            return redirect('MemeApp:home')
        else:
            messages.error(request, 'Невірне ім\'я користувача або пароль')
        return render(request, 'login.html')


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, 'Ви вийшли з акаунту')
        return redirect('MemeApp:home')


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        days_with_us = (timezone.now() - user.date_joined).days or 1

        user_memes = Meme.objects.filter(uploaded_by=user).order_by('-uploaded_at')
        created_memes_count = user_memes.count()

        total_likes = sum(meme.total_likes() for meme in user_memes)

        profile, created = UserProfile.objects.get_or_create(user=user)

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
    paginate_by = 12

    def get_queryset(self):
        queryset = Meme.objects.all().order_by('-uploaded_at')

        meme_type = self.request.GET.get('type')
        if meme_type:
            queryset = queryset.filter(meme_type=meme_type)

        sort_by = self.request.GET.get('sort', 'newest')
        if sort_by == 'popular':
            queryset = queryset.annotate(like_count=Count('likes')).order_by('-like_count', '-uploaded_at')
        elif sort_by == 'views':
            queryset = queryset.order_by('-views', '-uploaded_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'current_filter': self.request.GET.get('type'),
            'current_sort': self.request.GET.get('sort', 'newest')
        })
        return context


class UploadMemeView(LoginRequiredMixin, View):
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
        meme = get_object_or_404(Meme, id=meme_id)

        if request.user in meme.likes.all():
            meme.likes.remove(request.user)
            liked = False
        else:
            meme.likes.add(request.user)
            liked = True

        return JsonResponse({
            'liked': liked,
            'total_likes': meme.total_likes()
        })
        return redirect('MemeApp:meme_detail', pk=meme_id)


class DeleteProfileView(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user
        # Удаляем все мемы пользователя
        Meme.objects.filter(uploaded_by=user).delete()
        # Удаляем профиль
        UserProfile.objects.filter(user=user).delete()
        # Удаляем пользователя
        user.delete()

        logout(request)
        messages.success(request, 'Ваш профіль успішно видалено')
        return redirect('MemeApp:home')


class DeleteMemeView(LoginRequiredMixin, View):
    def post(self, request, meme_id):
        meme = get_object_or_404(Meme, id=meme_id)

        # Проверяем что пользователь является автором
        if meme.uploaded_by != request.user:
            return JsonResponse({'error': 'Недостатньо прав'}, status=403)

        meme_title = meme.title
        meme.delete()

        return JsonResponse({'success': True})

class EditProfileView(LoginRequiredMixin, View):
    def get(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        form = UserProfileForm(instance=profile)
        return render(request, 'edit_profile.html', {'form': form})

    def post(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профіль успішно оновлено!')
            return redirect('MemeApp:profile')
        return render(request, 'edit_profile.html', {'form': form})
