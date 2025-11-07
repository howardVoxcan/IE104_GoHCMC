// Kiểm tra chế độ hiện tại trong localStorage
const body = document.body;
const toggleBtn = document.getElementById('theme-toggle');

// Nếu đã lưu chế độ, thì áp dụng
if (localStorage.getItem('theme') === 'light') {
    body.classList.add('light-mode');
    toggleBtn.textContent = '☀️';
}

// Khi người dùng bấm nút chuyển
toggleBtn.addEventListener('click', () => {
    body.classList.toggle('light-mode');
    const isLight = body.classList.contains('light-mode');

    // Đổi biểu tượng và lưu trạng thái
    toggleBtn.textContent = isLight ? '☀️' : '🌙';
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
});
