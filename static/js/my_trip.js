(() => {
    const tripSuggestions = [
        "How about a food tour around District 1?",
        "Try visiting museums and cultural sites next!",
        "Plan a waterfront walk along the Saigon River.",
        "Explore the vibrant nightlife in District 2.",
        "Combine shopping and dining in a single trip!",
        "Visit historical landmarks for a heritage tour."
    ];

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            document.cookie.split(';').forEach(cookieStr => {
                const cookie = cookieStr.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                }
            });
        }
        return cookieValue;
    }

    document.addEventListener('DOMContentLoaded', () => {
        const cards = document.querySelectorAll('.trip-card');
        let totalDistance = 0;
        let totalDuration = 0;

        cards.forEach(card => {
            totalDistance += parseFloat(card.dataset.distance || 0);
            totalDuration += parseFloat(card.dataset.duration || 0);
        });

        const totalTrips = cards.length;
        const totalKm = totalDistance.toFixed(1);
        const totalHours = (totalDuration / 60).toFixed(1);
        const avgKm = totalTrips > 0 ? (totalDistance / totalTrips).toFixed(1) : 0;

        document.getElementById('total-trips').textContent = totalTrips;
        document.getElementById('total-distance').textContent = totalKm;
        document.getElementById('total-time').textContent = totalHours;
        document.getElementById('avg-distance').textContent = avgKm;

        const randomSuggestion = tripSuggestions[Math.floor(Math.random() * tripSuggestions.length)];
        document.getElementById('trip-suggestion').textContent = randomSuggestion;

        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                if (!confirm('Are you sure you want to delete this trip?')) return;
                fetch(this.dataset.url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                }).then(resp => {
                    if (!resp.ok) throw new Error('Delete failed');
                    this.closest('details')?.remove();
                }).catch(err => console.error(err));
            });
        });
    });
})();
