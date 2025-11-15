from django.shortcuts import render
import requests
import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import io
import base64
import numpy as np


# --- HÀM VẼ CHO 2 THEME ---
def generate_chart_image(periods_data, theme="light"):
    """
    Vẽ biểu đồ theo theme ('light' | 'dark') và trả về data URL base64
    """

    # 1) Trích xuất dữ liệu
    times = [p['time'] for p in periods_data]
    temps = [p['temp_c'] for p in periods_data]
    rains = [p['precip_mm'] for p in periods_data]

    # 2) Bảng màu khớp với CSS variables bạn đưa
    if theme == "dark":
        BG_COLOR = "#2C2C2C"       # var(--card-bg) trong dark
        TEXT_COLOR = "#ECF0F1"     # var(--text-main) trong dark
        ACCENT_COLOR = "#D35400"   # var(--accent) trong dark (nhiệt độ)
        RAIN_COLOR = "#27AE60"     # var(--primary) trong dark (mưa)
        BORDER_COLOR = "#555555"   # var(--border-color) trong dark
    else:
        BG_COLOR = "#FFFFFF"       # var(--card-bg) trong light
        TEXT_COLOR = "#2C3E50"     # var(--text-main) trong light
        ACCENT_COLOR = "#E67E22"   # var(--accent) trong light (nhiệt độ)
        RAIN_COLOR = "#2ECC71"     # var(--primary) trong light (mưa)
        BORDER_COLOR = "#E0E0E0"   # var(--border-color) trong light

    # 3) Figure/Axes
    fig, ax1 = plt.subplots(figsize=(12, 4), dpi=100)
    fig.patch.set_facecolor(BG_COLOR)
    ax1.set_facecolor(BG_COLOR)

    # === Trục Y1 (Nhiệt độ) ===
    ax1.plot(
        times, temps,
        color=ACCENT_COLOR, label='Temperature (°C)',
        marker='o', markersize=4, linestyle='-', zorder=3
    )
    ax1.fill_between(times, temps, color=ACCENT_COLOR, alpha=0.15, zorder=2)
    ax1.set_ylabel('Temperature (°C)', color=ACCENT_COLOR, fontsize=12)
    ax1.tick_params(axis='y', colors=ACCENT_COLOR)

    # === Trục Y2 (Mưa) ===
    ax2 = ax1.twinx()

    # 1) Dọn dữ liệu mưa: ép None -> 0, âm -> 0 (tránh kéo xuống dưới baseline)
    rains_clean = [max(0.0, float(r) if r is not None else 0.0) for r in rains]

    # 2) Vẽ đường & fill xuống baseline = 0
    ax2.plot(
        times, rains_clean,
        color=RAIN_COLOR, label='Rain (mm)',
        marker='o', markersize=4, linestyle='-', zorder=3
    )
    ax2.fill_between(times, rains_clean, 0, color=RAIN_COLOR, alpha=0.15, zorder=1)

    ax2.set_ylabel('Rain (mm)', color=RAIN_COLOR, fontsize=12)
    ax2.tick_params(axis='y', colors=RAIN_COLOR)

    # 3) Giới hạn Y cho mưa: “nice” gần max + headroom 10%
    max_r = max(rains_clean) if rains_clean else 0.0
    if max_r <= 0:
        y_max = 1.0
    else:
        exp = np.floor(np.log10(max_r))
        frac = max_r / (10 ** exp)
        for n in (1, 1.5, 2, 2.5, 5, 10):
            if frac <= n:
                nice = n * (10 ** exp)
                break
        y_max = float(nice) * 1.1  # chừa 10% không khí
    ax2.set_ylim(0, y_max)
    ax2.yaxis.set_major_locator(MaxNLocator(nbins=5))

    # === Trục X ===
    ax1.set_xticks(times[::2])
    ax1.set_xticklabels(times[::2], rotation=0, color=TEXT_COLOR)
    ax1.tick_params(axis='x', colors=TEXT_COLOR)

    # === Grid/Spines ===
    ax1.grid(color=BORDER_COLOR, linestyle='--', linewidth=0.5, alpha=0.6, zorder=0)
    ax2.grid(False)
    for spine in ['top', 'right', 'bottom', 'left']:
        ax1.spines[spine].set_color(BORDER_COLOR)
        ax2.spines[spine].set_color(BORDER_COLOR)
    ax1.spines['right'].set_visible(False)

    # === Legend chung ===
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    fig.legend(
        lines1 + lines2, labels1 + labels2,
        loc='upper center', bbox_to_anchor=(0.5, 1.05),
        ncol=2, frameon=False, labelcolor=TEXT_COLOR
    )

    # === Xuất base64 ===
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{image_base64}"


# --- VIEW CHÍNH ---
def weather(request):
    location = "10.762,106.6601"
    api_key = "5f170779de5e4c22b5542528252504"
    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days=3"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        location_name = data['location']['name']
        forecast_data = []

        for day in data['forecast']['forecastday']:
            raw_date = day['date']
            dt = datetime.datetime.strptime(raw_date, '%Y-%m-%d')
            formatted_date = dt.strftime('%a, %d %b')

            periods = []
            for h in day['hour'][::1]:
                hour_str = h['time'][11:13]
                periods.append({
                    'time': h['time'][11:],          # "HH:MM"
                    'hour': int(hour_str),           # dùng cho JS NOW
                    'temp_c': h['temp_c'],
                    'condition': h['condition']['text'],
                    'icon': h['condition']['icon'],
                    'precip_mm': h.get('precip_mm', 0),
                    'chance_of_rain': h.get('chance_of_rain', 0),
                    'humidity': h.get('humidity', 0),
                })

            # vẽ 2 theme
            chart_light = generate_chart_image(periods, theme="light")
            chart_dark  = generate_chart_image(periods, theme="dark")

            forecast_data.append({
                'date': formatted_date,
                'date_iso': raw_date,
                'periods': periods,
                'chart_image_light': chart_light,
                'chart_image_dark': chart_dark,
            })

        context = {'location_name': location_name, 'forecast': forecast_data}

    except Exception as e:
        print("Lỗi:", e)
        context = {'forecast': [], 'error': 'Không thể tải dữ liệu'}

    return render(request, 'page/weather/index.html', context)
