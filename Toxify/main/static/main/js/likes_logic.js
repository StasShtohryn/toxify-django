async function toggleLike(e, postId) {
    e.stopPropagation();

    const btn = document.getElementById(`like-btn-${postId}`);
    const icon = document.getElementById(`like-icon-${postId}`);
    const countEl = document.getElementById(`like-count-${postId}`);

    // Отримуємо CSRF токен
    const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;

    try {
        const res = await fetch(`/post/${postId}/like/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrf,
                'X-Requested-With': 'XMLHttpRequest',
            }
        });

        const data = await res.json();

        // Оновлюємо UI без перезавантаження
        countEl.textContent = data.count;

        if (data.liked) {
            icon.setAttribute('fill', 'currentColor');
            btn.classList.add('text-white');
            btn.classList.remove('text-white/40');
        } else {
            icon.setAttribute('fill', 'none');
            btn.classList.remove('text-white');
            btn.classList.add('text-white/40');
        }

    } catch (err) {
        console.error('Like error:', err);
    }
}


async function toggleCommentLike(btn, commentId) {
    const url = btn.dataset.url;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(res => res.json())
    .then(data => {
        const icon = btn.querySelector('.like-icon');
        const countEl = document.getElementById(`comment-like-count-${commentId}`);

        if (data.liked) {
            btn.classList.remove('text-white/40');
            btn.classList.add('text-white');
            icon.setAttribute('fill', 'currentColor');
        } else {
            btn.classList.remove('text-white');
            btn.classList.add('text-white/40');
            icon.setAttribute('fill', 'none');
        }

        countEl.textContent = data.count;
        btn.dataset.liked = data.liked;
    });
}