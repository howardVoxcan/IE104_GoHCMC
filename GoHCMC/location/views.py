from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from location.models import Location, Comment
from django.views.decorators.http import require_POST
from datetime import datetime
import joblib
import os
import spacy
from django.conf import settings
from django import template

register = template.Library()


@register.filter
def to(value, end):
    return range(value, end + 1)


nlp = spacy.load("en_core_web_sm")

pipeline_path = os.path.join(
    settings.BASE_DIR, 'location', 'svm_tfidf_pipeline.pkl')
label_encoder_path = os.path.join(
    settings.BASE_DIR, 'location', 'label_encoder.pkl')

pipeline = joblib.load(pipeline_path)
label_encoder = joblib.load(label_encoder_path)


def predict_sentiment(text):
    if not text or not isinstance(text, str):
        return "Invalid input"

    # Preprocess: lowercase + lemmatize + remove stop words
    doc = nlp(text.lower())
    tokens = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]
    cleaned_text = ' '.join(tokens)

    if not cleaned_text:
        return "Text too short or meaningless"

    # Predict using full pipeline
    pred_label = pipeline.predict([cleaned_text])[0]
    sentiment = label_encoder.inverse_transform([pred_label])[0]
    return sentiment


@require_POST
@login_required
def submit_comment_ajax(request, location_code):
    content = request.POST.get('content', '').strip()
    rating = request.POST.get('rating')
    location = get_object_or_404(Location, code=location_code)

    if not content:
        return JsonResponse({'error': 'Empty content'}, status=400)

    bot_reply = "Thanks for your comment!"  # Fallback reply

    if not rating:
        sentiment = predict_sentiment(content)
        if sentiment == "positive":
            bot_reply = "We're thrilled you had a great time! Hope to see you again!"
            rating = 4
        elif sentiment == "negative":
            bot_reply = "We're sorry to hear that. Your feedback helps us get better."
            rating = 2
        else:
            bot_reply = "Thank you for sharing your thoughts. We appreciate your input!"
            rating = 3
    else:
        rating = int(rating)
        if rating == 5:
            bot_reply = "Awesome! We're thrilled you loved it!"
        elif rating == 4:
            bot_reply = "Great! Glad you had a good time."
        elif rating == 3:
            bot_reply = "Thanks! We'll try to make your next visit even better."
        elif rating == 2:
            bot_reply = "Sorry to hear that. We hope things improve."
        elif rating == 1:
            bot_reply = "We sincerely apologize. Your feedback is valuable to us."
        else:
            bot_reply = "Thanks for your feedback!"

    comment = Comment.objects.create(
        location=location,
        user=request.user,
        content=content,
        rating=rating,
        bot_reply=bot_reply
    )

    return JsonResponse({
        'username': request.user.username,
        'content': comment.content,
        'bot_reply': comment.bot_reply
    })


def homepage(request):
    all_of_locations = Location.objects.order_by('-rating')[:12]
    user = request.user if request.user.is_authenticated else None
    top_locations = []
    for loc in all_of_locations:
        rating = (round(loc.rating * 2)) / 2
        full_stars = int(rating)
        has_half = (rating - full_stars) >= 0.5
        star_html = '<i class="fas fa-star"></i>' * full_stars

        if has_half:
            star_html += '<i class="fas fa-star-half-alt"></i>'
            empty_stars = 5 - full_stars - 1
        else:
            empty_stars = 5 - full_stars

        star_html += '<i class="far fa-star"></i>' * empty_stars

        favourite_symbol = (
            '<i class="fa-solid fa-heart"></i>'
            if user and loc.favourited_by.filter(id=user.id).exists()
            else '<i class="fa-regular fa-heart"></i>'
        )

        top_locations.append({
            'code': loc.code,
            'location': loc.location,
            'description': loc.description,
            'image_path': loc.image_path,
            'rating': loc.rating,
            'star_html': star_html,
            'favourite_symbol': favourite_symbol,
        })
    return render(request, "page/home/index.html", {
        'top_locations': top_locations
    })


def locations(request):
    # --- Xử lý POST: thêm/xóa yêu thích ---
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'unauthenticated'}, status=401)

        code = request.POST.get('value')
        if not code:
            return redirect('favourite')

        try:
            selected = Location.objects.get(code=code)
        except Location.DoesNotExist:
            return JsonResponse({'error': 'Location not found'}, status=404)

        user = request.user
        # Toggle trạng thái yêu thích
        if user in selected.favourited_by.all():
            selected.favourited_by.remove(user)
        else:
            selected.favourited_by.add(user)

        return redirect('locations')

    # --- Xử lý GET: hiển thị danh sách địa điểm ---
    else:
        type_filter = request.GET.get('type')
        min_rating = request.GET.get('rating')
        desired_time = request.GET.get('desired_time')
        search_query = request.GET.get('search')

        # --- Lấy page và limit ---
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        offset = (page - 1) * limit

        # --- Base query ---
        all_of_locations = Location.objects.all()

        # --- Lọc dữ liệu ---
        if type_filter:
            all_of_locations = all_of_locations.filter(
                type__iexact=type_filter)

        if min_rating:
            try:
                min_rating = float(min_rating)
                all_of_locations = all_of_locations.filter(
                    rating__gte=min_rating)
            except ValueError:
                pass

        if desired_time:
            try:
                desired_time_obj = datetime.strptime(
                    desired_time, "%H:%M").time()
                all_of_locations = all_of_locations.filter(
                    open_time__lte=desired_time_obj,
                    close_time__gte=desired_time_obj
                )
            except ValueError:
                pass

        if search_query:
            all_of_locations = all_of_locations.filter(
                Q(location__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(tags__icontains=search_query)
            )

        all_of_locations = all_of_locations.order_by('open_time')

        # --- Tính tổng số trang ---
        total_items = all_of_locations.count()
        total_pages = (total_items + limit - 1) // limit

        # --- Lấy dữ liệu trong trang hiện tại ---
        all_of_locations = all_of_locations[offset:offset + limit]

        user = request.user if request.user.is_authenticated else None

        # --- Xử lý dữ liệu cho template ---
        processed_locations = []
        for loc in all_of_locations:
            rating = (round(loc.rating * 2)) / 2
            full_stars = int(rating)
            has_half = (rating - full_stars) >= 0.5
            star_html = '<i class="fas fa-star"></i>' * full_stars

            if has_half:
                star_html += '<i class="fas fa-star-half-alt"></i>'
                empty_stars = 5 - full_stars - 1
            else:
                empty_stars = 5 - full_stars

            star_html += '<i class="far fa-star"></i>' * empty_stars

            favourite_symbol = (
                '<i class="fa-solid fa-heart"></i>'
                if user and loc.favourited_by.filter(id=user.id).exists()
                else '<i class="fa-regular fa-heart"></i>'
            )

            open_time = loc.open_time.strftime(
                "%H:%M") if loc.open_time else "N/A"
            close_time = loc.close_time.strftime(
                "%H:%M") if loc.close_time else "N/A"

            if open_time == "00:00" and close_time == "23:59":
                open_time_str = "All day"
            elif loc.close_time and loc.open_time and loc.close_time < loc.open_time:
                open_time_str = f"{open_time} - {close_time} (The next day)"
            else:
                open_time_str = f"{open_time} - {close_time}"

            processed_locations.append({
                'code': loc.code,
                'location': loc.location,
                'description': loc.description,
                'image_path': loc.image_path,
                'rating': loc.rating,
                'open_time': open_time_str,
                'star_html': star_html,
                'favourite_symbol': favourite_symbol,
            })

        # --- Render ra template ---
        return render(request, "page/locations/index.html", {
            'locations': processed_locations,
            'current_page': page,
            'total_pages': total_pages,
            'limit': limit,
            'current_filters': {
                'type': type_filter or '',
                'rating': min_rating or '',
                'desired_time': desired_time or '',
                'search': search_query or '',
            }
        })


def location_detail(request, location_code):
    location = get_object_or_404(Location, code=location_code)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        rating = request.POST.get('rating')

        if not content:
            return redirect('location_detail', location_code=location_code)

        bot_reply = "Thanks for your comment!"  # Default fallback reply

        if not rating:
            sentiment = predict_sentiment(content)
            if sentiment == "positive":
                bot_reply = "We're thrilled you had a great time! Hope to see you again!"
                rating = 4
            elif sentiment == "negative":
                bot_reply = "We're sorry to hear that. Your feedback helps us get better."
                rating = 2
            else:
                bot_reply = "Thank you for sharing your thoughts. We appreciate your input!"
                rating = 3
        else:
            try:
                rating = int(rating)
            except ValueError:
                rating = 3  # default rating if invalid

            if rating == 5:
                bot_reply = "Awesome! We're thrilled you loved it!"
            elif rating == 4:
                bot_reply = "Great! Glad you had a good time."
            elif rating == 3:
                bot_reply = "Thanks! We'll try to make your next visit even better."
            elif rating == 2:
                bot_reply = "Sorry to hear that. We hope things improve."
            elif rating == 1:
                bot_reply = "We sincerely apologize. Your feedback is valuable to us."
            else:
                bot_reply = "Thanks for your feedback!"

        Comment.objects.create(
            location=location,
            user=request.user,
            content=content,
            rating=rating,
            bot_reply=bot_reply
        )
        return redirect('display_location', location_code=location_code)

    else:
        # Lấy comment gốc (parent=None) và replies prefetch
        comments = Comment.objects.filter(location=location, parent=None).prefetch_related(
            'replies').order_by('-created_at')

        # Tính sao hiển thị
        rating = round(location.rating * 2) / 2 if location.rating else 0
        full_stars = int(rating)
        has_half = (rating - full_stars) >= 0.5
        star_html = '<i class="fas fa-star"></i>' * full_stars
        if has_half:
            star_html += '<i class="fas fa-star-half-alt"></i>'
            empty_stars = 5 - full_stars - 1
        else:
            empty_stars = 5 - full_stars
        star_html += '<i class="far fa-star"></i>' * empty_stars

        # Biểu tượng yêu thích (dựa trên nhiều trường hợp, ví dụ bạn lưu favourite ở Location.favourited_by M2M)
        if request.user.is_authenticated and location.favourited_by.filter(id=request.user.id).exists():
            favourite_symbol = '<i class="fa-solid fa-heart"></i>'
        else:
            favourite_symbol = '<i class="fa-regular fa-heart"></i>'

        # Xử lý thời gian mở cửa
        lat, long = location.coordinate.split(", ")
        open_time = location.open_time.strftime(
            "%H:%M") if location.open_time else "N/A"
        close_time = location.close_time.strftime(
            "%H:%M") if location.close_time else "N/A"

        if open_time == "00:00" and close_time == "23:59":
            open_time_str = "All day"
        elif location.close_time and location.open_time and location.close_time < location.open_time:
            open_time_str = f"{open_time} - {close_time} (The next day)"
        else:
            open_time_str = f"{open_time} - {close_time}"

        return render(request, "page/locations/detail.html", {
            "code": location.code,
            "location_name": location.location,
            "type": location.type,
            "open_time": open_time_str,
            "ticket_info": location.ticket_info,
            "address": location.address,
            "image_path": location.image_path,
            "long_description": location.long_description,
            "favourite_symbol": favourite_symbol,
            "lat": lat,
            "long": long,
            "star_html": star_html,
            "comments": comments,
            "location_obj": location  # dùng cho form POST
        })