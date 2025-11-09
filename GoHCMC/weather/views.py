from django.shortcuts import render
import requests
import datetime

# --- Thêm thư viện cho Matplotlib ---
import matplotlib
matplotlib.use('Agg') # Chuyển sang chế độ "backend" không cần GUI
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

# --- HÀM TẠO BIỂU ĐỒ (MỚI) ---
def generate_chart_image(periods_data):
    """
    Tạo biểu đồ từ dữ liệu 24h và trả về chuỗi base64
    """
    # --- 1. Trích xuất dữ liệu ---
    times = [p['time'] for p in periods_data]
    temps = [p['temp_c'] for p in periods_data]
    rains = [p['precip_mm'] for p in periods_data]

    # --- 2. Màu sắc (Dark Mode) ---
    BG_COLOR = "#3b3d40"
    TEXT_COLOR = "#bfc7cf"
    ACCENT_COLOR = "#FFB86C" # Nhiệt độ
    RAIN_COLOR = "#4FC3F7"   # Mưa
    BORDER_COLOR = "#555555"
    
    # --- 3. Tạo Figure và Axes ---
    fig, ax1 = plt.subplots(figsize=(12, 4), dpi=100)
    fig.patch.set_facecolor(BG_COLOR)
    ax1.set_facecolor(BG_COLOR)

    # --- 4. Vẽ Trục Y1 (Nhiệt độ) ---
    ax1.plot(times, temps, color=ACCENT_COLOR, label='Nhiệt độ (°C)', marker='o', markersize=4, linestyle='-')
    ax1.fill_between(times, temps, color=ACCENT_COLOR, alpha=0.15)
    ax1.set_ylabel('Nhiệt độ (°C)', color=ACCENT_COLOR, fontsize=12)
    ax1.tick_params(axis='y', colors=ACCENT_COLOR)

    # --- 5. Tạo Trục Y2 (Mưa) ---
    ax2 = ax1.twinx()
    ax2.plot(times, rains, color=RAIN_COLOR, label='Mưa (mm)', marker='o', markersize=4, linestyle='-')
    ax2.fill_between(times, rains, color=RAIN_COLOR, alpha=0.15)
    ax2.set_ylabel('Mưa (mm)', color=RAIN_COLOR, fontsize=12)
    ax2.tick_params(axis='y', colors=RAIN_COLOR)
    # Đặt giới hạn trục mưa
    max_rain = max(rains) if max(rains) > 0 else 1
    ax2.set_ylim(0, max_rain * 2) 

    # --- 6. Định dạng Trục X (Thời gian) ---
    # Chỉ hiển thị 8 nhãn (cứ 3 giờ 1 lần)
    ax1.set_xticks(times[::3])
    ax1.set_xticklabels(times[::3], rotation=0)
    ax1.tick_params(axis='x', colors=TEXT_COLOR)

    # --- 7. Định dạng chung (Grid, Spines) ---
    ax1.grid(color=BORDER_COLOR, linestyle='--', linewidth=0.5, alpha=0.5)
    ax2.grid(False) # Tắt grid trục 2
    
    for spine in ['top', 'right', 'bottom', 'left']:
        ax1.spines[spine].set_color(BORDER_COLOR)
        ax2.spines[spine].set_color(BORDER_COLOR)
    ax1.spines['right'].set_visible(False) # Ẩn spine trùng
    
    # --- 8. Legend ---
    # Tạo legend chung
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    legend = fig.legend(lines1 + lines2, labels1 + labels2, loc='upper center', 
                        bbox_to_anchor=(0.5, 1.05), ncol=2, frameon=False,
                        labelcolor=TEXT_COLOR)

    # --- 9. Lưu vào buffer và chuyển sang Base64 ---
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    
    return f"data:image/png;base64,{image_base64}"

# --- VIEW CHÍNH (Đã cập nhật) ---
def weather(request):
    location = "10.762,106.6601"
    api_key = "5f170779de5e4c22b5542528252504"
    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days=3"

    try:
        response = requests.get(url)
        data = response.json()

        location_name = data['location']['name']
        forecast_data = []

        for day in data['forecast']['forecastday']:
            raw_date = day['date']
            date_obj = datetime.datetime.strptime(raw_date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%a, %d %b') # → Mon, 23 Jun

            periods = []
            for hour_data in day['hour'][::1]: 
                periods.append({
                    'time': hour_data['time'][11:], 
                    'temp_c': hour_data['temp_c'],
                    'condition': hour_data['condition']['text'],
                    'icon': hour_data['condition']['icon'],
                    # **THÊM DỮ LIỆU MỚI cho card và chart**
                    'precip_mm': hour_data.get('precip_mm', 0),
                    'chance_of_rain': hour_data.get('chance_of_rain', 0)
                })

            # **TẠO BIỂU ĐỒ**
            chart_image_base64 = generate_chart_image(periods)

            forecast_data.append({
                'date': formatted_date,
                'periods': periods,
                'chart_image': chart_image_base64 # **THÊM ẢNH VÀO CONTEXT**
            })

        context = {
            'location_name': location_name,
            'forecast': forecast_data
        }

    except Exception as e:
        print(f"Lỗi: {e}")
        context = {'forecast': [], 'error': 'Không thể tải dữ liệu'}

    return render(request, 'page/weather/index.html', context)