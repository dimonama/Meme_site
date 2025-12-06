from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from PIL import Image
import os


class Meme(models.Model):
    MEME_TYPE_CHOICES = [
        ('image', '🏞️ Фото-мем'),
        ('video', '🎥 Відео-мем'),
    ]

    title = models.CharField(max_length=200, verbose_name="Назва мему")
    description = models.TextField(blank=True, verbose_name="Опис")

    file = models.FileField(
        upload_to='memes/%Y/%m/%d/',
        verbose_name="Файл",
        default='',  # ДОДАНО DEFAULT
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi', 'mov']
        )]
    )

    meme_type = models.CharField(
        max_length=20,
        choices=MEME_TYPE_CHOICES,
        default='image',
        verbose_name="Тип мему"
    )

    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата завантаження")
    likes = models.ManyToManyField(User, related_name='meme_likes', blank=True, verbose_name="Лайки")
    views = models.PositiveIntegerField(default=0, verbose_name="Перегляди")

    class Meta:
        verbose_name = "Мем"
        verbose_name_plural = "Меми"
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

    def total_likes(self):
        return self.likes.count()

    def increment_views(self):
        self.views += 1
        self.save()

    def save(self, *args, **kwargs):
        if self.file:
            file_name = self.file.name.lower()
            if any(file_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                self.meme_type = 'image'
            elif any(file_name.endswith(ext) for ext in ['.mp4', '.avi', '.mov']):
                self.meme_type = 'video'

        super().save(*args, **kwargs)

        if self.meme_type == 'image' and self.file:
            self.optimize_image()

    def optimize_image(self):
        try:
            img_path = self.file.path
            if os.path.exists(img_path):
                img = Image.open(img_path)

                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                if img.width > 1200:
                    new_height = int((1200 / img.width) * img.height)
                    img = img.resize((1200, new_height), Image.Resampling.LANCZOS)

                img.save(img_path, 'JPEG', quality=85, optimize=True)

        except Exception as e:
            print(f"Помилка оптимізації зображення: {e}")


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Користувач")
    avatar = models.ImageField(upload_to='avatars/%Y/%m/%d/', blank=True, null=True, verbose_name="Аватар")
    avatar_emoji = models.CharField(max_length=10, default='👤', verbose_name="Аватар (емодзі)")
    bio = models.TextField(max_length=500, blank=True, verbose_name="Біографія")
    location = models.CharField(max_length=100, blank=True, verbose_name="Місцезнаходження")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    class Meta:
        verbose_name = 'Профіль користувача'
        verbose_name_plural = 'Профілі користувачів'

    def __str__(self):
        return f"Профіль {self.user.username}"

    def get_total_memes(self):
        return self.user.meme_set.count()

    def get_total_likes_received(self):
        from django.db.models import Count
        result = Meme.objects.filter(uploaded_by=self.user).aggregate(
            total_likes=Count('likes')
        )
        return result['total_likes'] or 0

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

from django.db.models.signals import post_save
post_save.connect(create_user_profile, sender=User)