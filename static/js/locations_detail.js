document.getElementById("comment-form")?.addEventListener("submit", function (e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    fetch(form.getAttribute('action') || window.location.pathname, {
        method: "POST",
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]')?.value,
        },
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                const commentHTML = `
                <div class="comment">
                    <p><strong>${data.username}</strong>: ${data.content}</p>
                    <p><em>Bot reply:</em> ${data.bot_reply}</p>
                </div>
            `;
                document.getElementById("comments").insertAdjacentHTML('beforeend', commentHTML);
                form.reset();
            }
        })
        .catch(error => console.error("Error:", error));
});
