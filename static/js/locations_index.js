document.querySelectorAll('.fav-btn').forEach(function(button) {
  button.addEventListener('click', function(e) {
    e.preventDefault();
    const code = this.dataset.code;
    const icon = this.querySelector('i');

    fetch(window.location.pathname, {
      method: 'POST',
      headers: {
        'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]')?.value,
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: `value=${code}`
    })
    .then(response => {
      if (response.status === 401) {
        alert("Bạn cần đăng nhập để thêm vào danh sách yêu thích.");
        window.location.href = "/login/";
      } else if (response.ok) {
        icon.classList.toggle('fa-solid');
        icon.classList.toggle('fa-regular');
      } else {
        alert("Có lỗi xảy ra khi cập nhật favourite.");
      }
    })
    .catch(error => {
      console.error('Lỗi:', error);
      alert("Không thể kết nối với server.");
    });
  });
});
