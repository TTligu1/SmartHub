import io
import base64
import random
import qrcode
import barcode
import json
from barcode.writer import ImageWriter
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Max
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from PIL import Image, ImageOps
from .models import ChatSession, ChatMessage, TypingResult


# ==========================================
# 0. Ro'yxatdan o'tish sahifasi
# ==========================================
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Muvaffaqiyatli ro'yxatdan o'tdingiz! Endi tizimga kirishingiz mumkin. 🎉")
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


# 1. Bosh sahifa
def home(request):
    return render(request, 'core/home.html')


# 2. Barcha asboblar ro'yxati (Asboblar Paneli)
@login_required(login_url='login')
def tools_home(request):
    users_count = User.objects.count()
    return render(request, 'core/tools_list.html', {'users_count': users_count})


# 3. QR Kod yaratuvchi asbob
@login_required(login_url='login')
def qr_generator(request):
    qr_image = None
    text_data = ""

    if request.method == 'POST':
        text_data = request.POST.get('qr_text', '').strip()
        if text_data:
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(text_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            qr_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return render(request, 'core/qr_generator.html', {'qr_image': qr_image, 'text_data': text_data})


# 4. Shtrix Kod yaratuvchi asbob
@login_required(login_url='login')
def barcode_generator(request):
    barcode_image = None
    code_data = ""
    error_message = None

    if request.method == 'POST':
        code_data = request.POST.get('barcode_text', '').strip()
        if code_data:
            try:
                COD128 = barcode.get_by_name('code128', code_data, writer=ImageWriter())
                buffer = io.BytesIO()
                COD128.write(buffer)
                barcode_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            except Exception as e:
                error_message = "Xatolik: Iltimos, faqat standart harf va raqamlar kiriting!"

    return render(request, 'core/barcode_generator.html', {
        'barcode_image': barcode_image,
        'code_data': code_data,
        'error_message': error_message
    })


# 5. AI Chatbot (LIMIT VA PREMIUM BILAN YANGILANGAN VERSIYASI)
@login_required(login_url='login')
def ai_chat(request):
    user = request.user
    sessions = ChatSession.objects.filter(user=user)

    session_id = request.GET.get('session_id')
    active_session = None

    if session_id:
        active_session = ChatSession.objects.filter(id=session_id, user=user).first()

    if not active_session:
        active_session = sessions.first()
        if not active_session:
            active_session = ChatSession.objects.create(user=user, title="Yangi suhbat 🧠")
            ChatMessage.objects.create(
                session=active_session,
                sender="ai",
                text="Salom! Men SmartHub AI yordamchisiman. Bugun sizga qanday yordam bera olaman? 🧠"
            )

    # SHU YERDA CHEKLOV MANTIQI BOSHLANADI:
    # Foydalanuvchi yuborgan (sender="user") xabarlar sonini sanaymiz
    user_messages_count = active_session.messages.filter(sender="user").count()
    CHAT_LIMIT = 5  # Bitta suhbat uchun xabarlar limiti
    limit_reached = user_messages_count >= CHAT_LIMIT

    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()

        # Yangi suhbat ochish tugmasi bosilganda
        if 'new_chat' in request.POST:
            active_session = ChatSession.objects.create(user=user, title="Yangi suhbat 🧠")
            ChatMessage.objects.create(
                session=active_session,
                sender="ai",
                text="Salom! Men yangi suhbatga tayyorman. Savolingizni bering! 🧠"
            )
            return redirect(f'/ai-chat/?session_id={active_session.id}')

        # Agar limit tugagan bo'lsa va foydalanuvchi yana xabar yozmoqchi bo'lsa, xabarni saqlamaymiz
        if limit_reached:
            return render(request, 'core/ai_chat.html', {
                'sessions': ChatSession.objects.filter(user=user),
                'active_session': active_session,
                'chat_history': active_session.messages.all(),
                'limit_reached': True,
                'chat_limit': CHAT_LIMIT
            })

        if user_message:
            # Xabarni saqlash
            ChatMessage.objects.create(session=active_session, sender="user", text=user_message)

            # Sarlavhani avtomatik o'zgartirish
            if active_session.title.startswith("Yangi suhbat"):
                truncated_title = user_message[:25] + "..." if len(user_message) > 25 else user_message
                active_session.title = truncated_title
                active_session.save()

            # AI javob logikasi
            msg_lower = user_message.lower()
            if "salom" in msg_lower or "assalom" in msg_lower:
                ai_response = random.choice([
                    "Vaalaykum assalom! Kuningiz xayrli o'tsin! 😊",
                    "Salom! Ishlaringiz yaxshimi? SmartHub-ga xush kelibsiz! ✨"
                ])
            elif "ism" in msg_lower or "kim" in msg_lower:
                ai_response = "Mening ismim SmartHub AI. Men sizga yordam berish uchun shu yerdaman! 🤖"
            elif "qanday" in msg_lower or "yaxshimi" in msg_lower:
                ai_response = "Men sun'iy intellektman, doim a'lo kayfiyatdaman! O'zingizda nima gaplar? 😎"
            elif "rahmat" in msg_lower:
                ai_response = "Sizga ham katta rahmat! Yordam bera olganimdan xursandman. 🌟"
            elif "yaratdi" in msg_lower or "avtor" in msg_lower:
                ai_response = "Mening yaratuvchim — siz! Juda zo'r dasturchisiz! 💻⚡"
            else:
                ai_response = f"Siz '{user_message}' deb yozdingiz. Men hali o'rganish jarayonidaman! 😉"

            ChatMessage.objects.create(session=active_session, sender="ai", text=ai_response)

            # Xabar yuborilgandan keyin hisoblagichni yangilaymiz
            user_messages_count = active_session.messages.filter(sender="user").count()
            limit_reached = user_messages_count >= CHAT_LIMIT

    return render(request, 'core/ai_chat.html', {
        'sessions': sessions,
        'active_session': active_session,
        'chat_history': active_session.messages.all() if active_session else [],
        'limit_reached': limit_reached,
        'chat_limit': CHAT_LIMIT,
        'user_messages_count': user_messages_count
    })


# 6. PDF Asboblar
@login_required(login_url='login')
def pdf_tools(request):
    result_file = None
    action_type = None
    success_message = None

    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        uploaded_file = request.FILES.get('pdf_file')

        if uploaded_file:
            if action_type == 'to_word':
                success_message = f"'{uploaded_file.name}' fayli muvaffaqiyatli Word (.docx) formatiga o'tkazildi!"
                result_file = "smarthub_converted.docx"
            elif action_type == 'merge':
                success_message = "Yuklangan PDF fayllari muvaffaqiyatli bitta hujjatga birlashtirildi!"
                result_file = "smarthub_merged.pdf"
            elif action_type == 'split':
                success_message = "PDF hujjat muvaffaqiyatli alohida sahifalarga ajratildi!"
                result_file = "smarthub_split_pages.zip"

    return render(request, 'core/pdf_tools.html', {
        'result_file': result_file,
        'action_type': action_type,
        'success_message': success_message
    })


# 7. Rasm Instrumentlari
@login_required(login_url='login')
def image_tools(request):
    result_image = None
    success_message = None
    file_name = "smarthub_image.png"

    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        uploaded_image = request.FILES.get('image_file')

        if uploaded_image:
            try:
                input_image = Image.open(uploaded_image)
                output_buffer = io.BytesIO()

                if action_type == 'bg_remover':
                    processed_image = ImageOps.grayscale(input_image)
                    processed_image.save(output_buffer, format="PNG")
                    result_image = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
                    success_message = f"'{uploaded_image.name}' fayliga muvaffaqiyatli effekt berildi!"
                    file_name = "smarthub_effect.png"

                elif action_type == 'compressor':
                    input_image.convert('RGB').save(output_buffer, format="JPEG", quality=30)
                    result_image = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
                    success_message = f"'{uploaded_image.name}' hajmi muvaffaqiyatli siqildi!"
                    file_name = "smarthub_compressed.jpg"

                elif action_type == 'crop':
                    width, height = input_image.size
                    min_dim = min(width, height)
                    left = (width - min_dim) / 2
                    top = (height - min_dim) / 2
                    right = (width + min_dim) / 2
                    bottom = (height + min_dim) / 2

                    cropped_image = input_image.crop((left, top, right, bottom))
                    cropped_image.save(output_buffer, format="PNG")
                    result_image = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
                    success_message = f"'{uploaded_image.name}' muvaffaqiyatli qirqildi!"
                    file_name = "smarthub_cropped.png"

            except Exception as e:
                success_message = f"Xatolik yuz berdi: {str(e)}"
                result_image = None

    return render(request, 'core/image_tools.html', {
        'result_image': result_image,
        'success_message': success_message,
        'file_name': file_name
    })


# --- KLAVIATURA POYGASI QISMI ---
TEXT_POOL = [
    "Dasturlashni o'rganish sabr va tinimsiz mehnat talab qiladi. Har kuni ozgina bo'lsa ham kod yozing.",
    "Python juda sodda va tushunarli dasturlash tili bo'lib, u sun'iy intellekt sohasida keng qo'llaniladi.",
    "Django loyihani tezkor va xavfsiz tarzda ishlab chiqish uchun eng mukammal veb freymvorklardan biridir."
]


@login_required(login_url='login')
def race_arena(request):
    random_text = random.choice(TEXT_POOL)
    return render(request, 'core/race_arena.html', {'text_to_type': random_text})


@login_required(login_url='login')
def races_list(request):
    top_results = TypingResult.objects.values('user').annotate(max_wpm=Max('wpm')).order_by('-max_wpm')[:10]
    leaderboard = []
    for entry in top_results:
        result = TypingResult.objects.filter(user_id=entry['user'], wpm=entry['max_wpm']).first()
        if result:
            leaderboard.append(result)
    return render(request, 'core/races_list.html', {'leaderboard': leaderboard})


@login_required(login_url='login')
def save_race_result(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_wpm = int(data.get('wpm', 0))
            new_accuracy = int(data.get('accuracy', 0))
            if new_wpm <= 0:
                return JsonResponse({'status': 'ignored'})
            highest_wpm = TypingResult.objects.filter(user=request.user).aggregate(Max('wpm'))['wpm__max']
            if highest_wpm is None or new_wpm > highest_wpm:
                TypingResult.objects.create(user=request.user, wpm=new_wpm, accuracy=new_accuracy)
                return JsonResponse({'status': 'success'})
            return JsonResponse({'status': 'ignored'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)


@login_required(login_url='login')
def ai_chat(request):
    user = request.user

    # Foydalanuvchi profilini tekshiramiz (Premium yoki yo'qligini bilish uchun)
    # Agar profil hali yaratilmagan bo'lsa, avtomatik yaratib ketadi
    profile, created = UserProfile.objects.get_or_create(user=user)

    sessions = ChatSession.objects.filter(user=user)
    session_id = request.GET.get('session_id')
    active_session = None

    if session_id:
        active_session = ChatSession.objects.filter(id=session_id, user=user).first()

    if not active_session:
        active_session = sessions.first()
        if not active_session:
            active_session = ChatSession.objects.create(user=user, title="Yangi suhbat 🧠")
            ChatMessage.objects.create(
                session=active_session,
                sender="ai",
                text="Salom! Men SmartHub AI yordamchisiman. Bugun sizga qanday yordam bera olaman? 🧠"
            )

    # Xabarlar sonini hisoblaymiz
    user_messages_count = active_session.messages.filter(sender="user").count()
    CHAT_LIMIT = 5

    # AGAR FOYDALANUVCHI PREMIUM BO'LSA - LIMIT HECH QACHON TUGAMAYDI!
    if profile.is_premium:
        limit_reached = False
    else:
        limit_reached = user_messages_count >= CHAT_LIMIT

    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()

        if 'new_chat' in request.POST:
            active_session = ChatSession.objects.create(user=user, title="Yangi suhbat 🧠")
            ChatMessage.objects.create(
                session=active_session,
                sender="ai",
                text="Salom! Men yangi suhbatga tayyorman. Savolingizni bering! 🧠"
            )
            return redirect(f'/ai-chat/?session_id={active_session.id}')

        if limit_reached:
            return render(request, 'core/ai_chat.html', {
                'sessions': ChatSession.objects.filter(user=user),
                'active_session': active_session,
                'chat_history': active_session.messages.all(),
                'limit_reached': True,
                'chat_limit': CHAT_LIMIT,
                'is_premium': profile.is_premium
            })

        if user_message:
            ChatMessage.objects.create(session=active_session, sender="user", text=user_message)

            if active_session.title.startswith("Yangi suhbat"):
                truncated_title = user_message[:25] + "..." if len(user_message) > 25 else user_message
                active_session.title = truncated_title
                active_session.save()

            # Sun'iy javoblar...
            msg_lower = user_message.lower()
            if "salom" in msg_lower or "assalom" in msg_lower:
                ai_response = "Vaalaykum assalom! Kuningiz xayrli o'tsin! 😊"
            elif "ism" in msg_lower:
                ai_response = "Mening ismim SmartHub AI. 🤖"
            else:
                ai_response = f"Siz '{user_message}' deb yozdingiz. Men hali o'rganish jarayonidaman! 😉"

            ChatMessage.objects.create(session=active_session, sender="ai", text=ai_response)

            user_messages_count = active_session.messages.filter(sender="user").count()
            if profile.is_premium:
                limit_reached = False
            else:
                limit_reached = user_messages_count >= CHAT_LIMIT

    return render(request, 'core/ai_chat.html', {
        'sessions': sessions,
        'active_session': active_session,
        'chat_history': active_session.messages.all() if active_session else [],
        'limit_reached': limit_reached,
        'chat_limit': CHAT_LIMIT,
        'user_messages_count': user_messages_count,
        'is_premium': profile.is_premium  # Shablonda yulduzcha chiqarish uchun
    })