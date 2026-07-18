from django.db import models
from django.contrib.auth.models import User

# Chat sessiyasi (har bir alohida suhbat uchun)
class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=100, default="Yangi suhbat")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

# Suhbat ichidagi xabarlar
class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10)  # 'user' yoki 'ai'
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class TypingResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Foydalanuvchi")
    wpm = models.IntegerField(verbose_name="Tezlik (WPM)")
    accuracy = models.IntegerField(verbose_name="Anriqlik (%)")
    date_earned = models.DateTimeField(auto_now_add=True, verbose_name="Sana")

    class Meta:
        ordering = ['-wpm', '-accuracy']

    def __str__(self):
        return f"{self.user.username} - {self.wpm} WPM"


# XATO TO'G'RILANDI: Leaderboard endi TypingResult ichida emas, alohida model bo'ldi
class Leaderboard(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # OneToOneField bitta odamga faqat 1 ta qator ochishga majburlaydi
    wpm = models.IntegerField(default=0)
    accuracy = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now=True)  # Har safar yangilansa, vaqt avtomat o'zgaradi

    def __str__(self):
        return f"{self.user.username} - {self.wpm} WPM"


# XATO TO'G'RILANDI: Takroriy importlar olib tashlandi
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_premium = models.BooleanField(default=False)  # True bo'lsa - cheksiz yozadi, False bo'lsa - limitli

    def __str__(self):
        return f"{self.user.username} - Premium: {self.is_premium}"