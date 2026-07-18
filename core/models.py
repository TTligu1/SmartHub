from django.db import models
from django.contrib.auth.models import User

# ==========================================
# 💎 1. FOYDALANUVCHI PROFILLI MODELI (PREMIUM CHEKLOVLAR UCHUN)
# ==========================================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_premium = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {'Premium' if self.is_premium else 'Oddiy'}"


# ==========================================
# 🤖 2. SUN'IY INTELLEKT (AI CHATBOT) MODELLARI
# ==========================================
class ChatSession(models.Model):
    """ AI bilan bo'lgan har bir alohida suhbat sessiyasi """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=100, default="Yangi suhbat")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class ChatMessage(models.Model):
    """
    AI suhbat ichidagi xabarlar.
    views.py faylidagi AI bot qismiga moslashishi uchun nomi o'zgartirilmadi,
    lekin maydonlari saqlab qolindi.
    """
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10)  # 'user' yoki 'ai'
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    @property
    def timestamp(self):
        return self.created_at


# ==========================================
# 💬 3. INTEGRATSIYA QILINGAN TELEGRAM CHAT MODELI
# ==========================================
class TelegramChatMessage(models.Model):
    """ Foydalanuvchilar o'rtasidagi Shaxsiy va Hamma uchun ochiq Umumiy chat xabarlari """
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tg_sent_messages')
    # Agar receiver null (bo'sh) bo'lsa, bu hamma uchun ochiq "Umumiy Chat" hisoblanadi
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tg_received_messages', null=True, blank=True)
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        if self.receiver:
            return f"{self.sender.username} -> {self.receiver.username}: {self.message_text[:20]}"
        return f"[Umumiy Chat] {self.sender.username}: {self.message_text[:20]}"


# ==========================================
# ⌨️ 4. TEZ YOZAR (KLAVIATURA POYGASI) MODELLARI
# ==========================================
class TypingResult(models.Model):
    """ Har bir urinishdagi tezlik natijasi """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Foydalanuvchi")
    wpm = models.IntegerField(verbose_name="Tezlik (WPM)")
    accuracy = models.IntegerField(verbose_name="Anriqlik (%)")
    date_earned = models.DateTimeField(auto_now_add=True, verbose_name="Sana")

    class Meta:
        ordering = ['-wpm', '-accuracy']

    def __str__(self):
        return f"{self.user.username} - {self.wpm} WPM"


class Leaderboard(models.Model):
    """ Foydalanuvchining eng yuqori rekordlar jadvali """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wpm = models.IntegerField(default=0)
    accuracy = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.wpm} WPM"