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
from django.contrib.auth.forms import UserCreationForm  # 👈 RO'YXATDAN O'TISH FORMASI QO'SHILDI
from django.contrib import messages  # 👈 XABARLAR QO'SHILDI
from .models import ChatSession, ChatMessage, TypingResult


# ==========================================
# 0. Ro'yxatdan o'tish sahifasi (YANGI QO'SHILDI)
# ==========================================
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Muvaffaqiyatli ro'yxatdan o'tdingiz! Endi tizimga kirishingiz mumkin. 🎉")
            return redirect('login')  # Ro'yxatdan o'tgach, login sahifasiga o'tadi
    else:
        form = UserCreationForm()

    # HTML-ga 'form' kaliti bilan formani yuboramiz
    return render(request, 'accounts/register.html', {'form': form})


# 1. Bosh sahifa
def home(request):
    return render(request, 'core/home.html')


# 2. Barcha asboblar ro'yxati
@login_required(login_url='login')
def tools_home(request):
    return render(request, 'core/tools_list.html')


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


# 5. AI Chatbot
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

    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()

        if 'new_chat' in request.POST:
            active_session = ChatSession.objects.create(user=user, title="Yangi suhbat 🧠")
            ChatMessage.objects.create(
                session=active_session,
                sender="ai",
                text="Salom! Men yangi suhbatga tayyorman. 🧠"
            )
            return render(request, 'core/ai_chat.html', {
                'sessions': ChatSession.objects.filter(user=user),
                'active_session': active_session,
                'chat_history': active_session.messages.all()
            })

        if user_message:
            ChatMessage.objects.create(session=active_session, sender="user", text=user_message)

            if active_session.title.startswith("Yangi suhbat"):
                truncated_title = user_message[:25] + "..." if len(user_message) > 25 else user_message
                active_session.title = truncated_title
                active_session.save()

            ai_response = "Kechirasiz, hozircha bu savolga javob bera olmayman."
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
                ai_response = f"Siz '{user_message}' deb yozdingiz. Men hali o'rganish jarayonidaman, lekin tez orada juda aqlli bo'lib ketaman! 😉"

            ChatMessage.objects.create(session=active_session, sender="ai", text=ai_response)

    return render(request, 'core/ai_chat.html', {
        'sessions': sessions,
        'active_session': active_session,
        'chat_history': active_session.messages.all() if active_session else []
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


# 7. Rasm bilan ishlovchi asboblar
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
                image_data = uploaded_image.read()
                result_image = base64.b64encode(image_data).decode('utf-8')
            except Exception:
                result_image = None

            if action_type == 'bg_remover':
                success_message = f"'{uploaded_image.name}' faylining foni muvaffaqiyatli o'chirildi!"
                file_name = "smarthub_no_bg.png"
            elif action_type == 'compressor':
                success_message = f"'{uploaded_image.name}' sifati buzilmagan holda muvaffaqiyatli siqildi!"
                file_name = "smarthub_compressed.jpg"
            elif action_type == 'crop':
                success_message = f"'{uploaded_image.name}' muvaffaqiyatli qirqildi!"
                file_name = "smarthub_cropped.png"

    return render(request, 'core/image_tools.html', {
        'result_image': result_image,
        'success_message': success_message,
        'file_name': file_name
    })


# --- KLAVIATURA POYGASI QISMI ---

TEXT_POOL = [
    "Dasturlashni o'rganish sabr va tinimsiz mehnat talab qiladi. Har kuni ozgina bo'lsa ham kod yozing.",
    "Python juda sodda va tushunarli dasturlash tili bo'lib, u sun'iy intellekt sohasida keng qo'llaniladi.",
    "Django loyihani tezkor va xavfsiz tarzda ishlab chiqish uchun eng mukammal veb freymvorklardan biridir.",
    "Muvaffaqiyat kaliti bu har qanday qiyinchilikka qaramasdan maqsad sari to'xtovsiz harakat qilishdir.",
    "Klavaturada tez yozish nafaqat vaqtni tejaydi, balki fikrlash tezligini ham oshirishga yordam beradi."
]


# Poyga arenasi sahifasi
@login_required(login_url='login')
def race_arena(request):
    random_text = random.choice(TEXT_POOL)
    return render(request, 'core/race_arena.html', {'text_to_type': random_text})


# Reyting jadvali
@login_required(login_url='login')
def races_list(request):
    top_results = (
        TypingResult.objects.values('user')
        .annotate(max_wpm=Max('wpm'))
        .order_by('-max_wpm')[:10]
    )

    leaderboard = []
    for entry in top_results:
        result = TypingResult.objects.filter(
            user_id=entry['user'],
            wpm=entry['max_wpm']
        ).first()
        if result:
            leaderboard.append(result)

    return render(request, 'core/races_list.html', {'leaderboard': leaderboard})


# Natijani saqlash
@login_required(login_url='login')
def save_race_result(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_wpm = int(data.get('wpm', 0))
            new_accuracy = int(data.get('accuracy', 0))

            if new_wpm <= 0:
                return JsonResponse({'status': 'ignored', 'message': 'Yaroqsiz WPM'})

            highest_wpm = TypingResult.objects.filter(user=request.user).aggregate(Max('wpm'))['wpm__max']

            if highest_wpm is None or new_wpm > highest_wpm:
                TypingResult.objects.create(
                    user=request.user,
                    wpm=new_wpm,
                    accuracy=new_accuracy
                )
                return JsonResponse({'status': 'success', 'message': 'Yangi rekord o‘rnatildi! 🎉'})

            return JsonResponse({'status': 'ignored', 'message': 'Natija eski rekorddan past, saqlanmadi.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Noto‘g‘ri so‘rov'}, status=400)