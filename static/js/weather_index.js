function updateNowIndicator() {
    const now = new Date();
    const currentHour = now.getHours();
    const currentDate = now.toISOString().split('T')[0];

    document.querySelectorAll('.now-indicator').forEach(el => el.remove());
    document.querySelectorAll('.forecast-period.is-now').forEach(el => {
        el.classList.remove('is-now');
    });

    let foundCurrentBox = false;
    document.querySelectorAll('.forecast-period').forEach(box => {
        const boxHour = parseInt(box.getAttribute('data-hour'));
        const boxDate = box.getAttribute('data-date');
        const boxTime = box.getAttribute('data-time');

        if (boxDate === currentDate && boxHour === currentHour) {
            foundCurrentBox = true;
            box.classList.add('is-now');
            const nowBadge = document.createElement('span');
            nowBadge.className = 'now-indicator';
            nowBadge.textContent = 'NOW';
            box.appendChild(nowBadge);

            setTimeout(() => {
                const container = box.closest('.detail-box-container');
                if (container) {
                    const boxLeft = box.offsetLeft;
                    const boxWidth = box.offsetWidth;
                    const containerWidth = container.offsetWidth;
                    const scrollPosition = boxLeft - (containerWidth / 2) + (boxWidth / 2);

                    container.scrollTo({
                        left: Math.max(0, scrollPosition),
                        behavior: 'smooth'
                    });
                }
            }, 300);
        }
    });
}

function switchDay(dayIndex) {
    document.querySelectorAll('.forecast-display').forEach((panel, i) => {
        panel.classList.toggle('active', i === dayIndex);
    });
    document.querySelectorAll('.tab-btn').forEach((btn, i) => {
        btn.classList.toggle('active', i === dayIndex);
    });
    setTimeout(() => {
        updateNowIndicator();
        updateScrollButtons(dayIndex);
    }, 50);
}

function scrollHourly(dayIndex, direction) {
    const container = document.getElementById('hourly-container-' + dayIndex);
    if (!container) return;

    const boxes = container.querySelectorAll('.forecast-period');
    if (boxes.length === 0) return;

    const boxWidth = boxes[0].offsetWidth;
    const gap = parseFloat(getComputedStyle(container).gap) || 16;
    const scrollDistance = (boxWidth + gap) * Math.abs(direction);

    container.scrollBy({
        left: direction > 0 ? scrollDistance : -scrollDistance,
        behavior: 'smooth'
    });

    setTimeout(() => updateScrollButtons(dayIndex), 400);
}

function updateScrollButtons(dayIndex) {
    const container = document.getElementById('hourly-container-' + dayIndex);
    if (!container) return;

    const leftBtn = document.getElementById('scroll-left-' + dayIndex);
    const rightBtn = document.getElementById('scroll-right-' + dayIndex);

    if (leftBtn && rightBtn) {
        const maxScroll = container.scrollWidth - container.clientWidth;
        leftBtn.disabled = container.scrollLeft <= 5;
        rightBtn.disabled = container.scrollLeft >= maxScroll - 5;
    }
}

document.addEventListener('DOMContentLoaded', function () {
    updateNowIndicator();

    document.querySelectorAll('.scroll-btn-left, .scroll-btn-right').forEach(btn => {
        btn.addEventListener('click', () => {
            const day = parseInt(btn.getAttribute('data-day'));
            const dir = parseInt(btn.getAttribute('data-direction'));
            if (!isNaN(day) && !isNaN(dir)) {
                scrollHourly(day, dir);
            }
        });
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const day = parseInt(btn.getAttribute('data-day'));
            if (!isNaN(day)) {
                switchDay(day);
            }
        });
    });

    document.querySelectorAll('.forecast-display').forEach((display, index) => {
        updateScrollButtons(index);
        const container = display.querySelector('.detail-box-container');
        if (container) {
            container.addEventListener('scroll', () => updateScrollButtons(index));
        }
    });

    setInterval(() => {
        updateNowIndicator();
    }, 30000);

    setInterval(() => {
        updateNowIndicator();
    }, 60000);
});

document.addEventListener('visibilitychange', function () {
    if (!document.hidden) {
        updateNowIndicator();
    }
});
