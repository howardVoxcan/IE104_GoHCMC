document.addEventListener('DOMContentLoaded', function() {
  fetch('/static/data/Banner.json')
    .then(res => res.json())
    .then(banners => {
      let idx = 0;
      const img = document.getElementById('banner-img');
      const title = document.getElementById('banner-title');
      const desc = document.getElementById('banner-desc');
      function showBanner(i) {
        img.src = banners[i].img;
        title.textContent = banners[i].title;
        desc.textContent = banners[i].desc;
      }
      showBanner(idx);
      setInterval(() => {
        idx = (idx + 1) % banners.length;
        showBanner(idx);
      }, 5000);
    });
});
