# Toxify — короткі коментарі до коду

## 📁 Структура проєкту

- **posts/** — пости, коментарі, реакції, сповіщення, репорти
- **profiles/** — користувачі, профілі, підписки, репости
- **main/** — головний шаблон, модалки, сторінка "About"
- **utils/** — завантаження файлів у Vercel Blob

---

## 🔵 posts/models.py

| Модель | Опис |
|--------|------|
| **Hashtag** | Хештег. Унікальна назва (#toxic, #drama). |
| **Post** | Пост: автор (Profile), заголовок, текст, зображення, хештеги. Методи: `get_last_main_comment()`, `toxic_count`, `cringe_count`, `based_count`, `user_current_reaction()`. |
| **Comment** | Коментар: автор, пост, текст, parent (для відповідей). Підтримка вкладеності через `parent`. |
| **PostLike** | Лайк поста. Один юзер = один лайк. unique_together (profile, post). |
| **CommentLike** | Лайк коментаря. unique_together (profile, comment). |
| **Reaction** | Реакція на пост: toxic / cringe / based. Впливає на reputation автора. |
| **CommentReaction** | Реакція на коментар (аналог Reaction). |
| **Report** | Скарга на пост або коментар. reporter, reason. |
| **Notification** | Сповіщення: recipient, sender, post, message, is_read. |

---

## 🔵 profiles/models.py

| Модель | Опис |
|--------|------|
| **User** | Користувач (AbstractUser). |
| **Profile** | Профіль: name, avatar, bio, following (підписки), toxicity_level, reputation_score. Методи: `is_following()`, `recalculate_toxicity()`, `has_unread_notifications`. |
| **Repost** | Репост поста. profile + post, unique_together. |

---

## 🔵 posts/views.py

### Допоміжні функції

| Функція | Що робить |
|---------|-----------|
| `_get_mentioned_usernames(text)` | Витягує з тексту всі @username (regex). |
| `_create_mention_notifications(...)` | Створює Notification для кожного згаданого користувача. |
| `_add_liked_to_posts(request, posts)` | Додає на кожен пост атрибути `user_has_liked` та `user_has_reposted`. |

### View-класи та функції

| View / функція | URL | Опис |
|----------------|-----|------|
| **SearchView** | `/search/?q=` | Пошук: по хештегу (#), юзернейму (@), або по тексту. |
| **PostsListView** | `/` | Головна. Список постів, останній коментар, лайки. |
| **PostDetailView** | `/post/<id>/` | Сторінка поста з усіма коментарями. |
| **PostCreateView** | `/create/<username>/` | Створення поста. Парсить хештеги, створює mention-сповіщення. |
| **PostDeleteView** | `/post/<id>/delete/` | Видалення поста. Тільки автор. |
| **CommentCreateView** | `/post/<id>/comment/<username>/` | Створення коментаря. Підтримує parent_id для відповідей. |
| **LikePostToggleView** | `/post/<id>/like/` | Поставити / зняти лайк поста. |
| **LikeCommentToggleView** | `/comment/<id>/like/` | Поставити / зняти лайк коментаря. |
| `toggle_reaction` | `/post/<id>/react/<type>/` | Реакція на пост (toxic/cringe/based). Змінює reputation. |
| `toggle_comment_reaction` | `/comment/<id>/react/<type>/` | Реакція на коментар. |
| `report_post` | `/post/<id>/report/` | Скарга на пост. 2+ скарги → пост видаляється. |
| `report_comment` | `/comment/<id>/report/` | Скарга на коментар. 3+ скарги → коментар видаляється. |
| `notifications_list` | `/notifications/` | Список сповіщень. Позначає їх прочитаними. |
| `delete_comment` | `/comment/<id>/delete/` | Видалення коментаря. |
| `edit_post` | `/post/<id>/edit/` | Редагування поста. |

---

## 🔵 profiles/views.py

| View / функція | URL | Опис |
|----------------|-----|------|
| **RegisterView** | `/profile/register/` | Реєстрація. Створює User + Profile, логінить. |
| **ProfileDetailView** | `/profile/users/<username>/` | Публічний профіль. Пости, репости, відповіді. |
| **ProfileEditView** | `/profile/edit/` | Редагування профілю (avatar, bio) та акаунту (username). |
| **FollowToggleView** | `/profile/users/<username>/follow/` | Підписатись / відписатись. AJAX або redirect. |
| **RepostToggleView** | `/profile/posts/<id>/repost/` | Репост / відміна репоста. AJAX або redirect. |
| `user_search_api` | `/profile/api/users/search/?q=` | API для пошуку юзерів (для @mention). Повертає JSON. |

---

## 🔵 utils/blobs.py

| Функція | Що робить |
|---------|-----------|
| `upload_to_vercel_blob(file, folder)` | Завантажує файл у Vercel Blob. folder: `avatars`, `posts`, `comments`. Повертає URL. |
| `delete_from_vercel_blob(url)` | Видаляє файл з Blob за URL. Не чіпає default.jpg. |

---

## 🔵 main/templatetags/mention_filters.py

| Фільтр | Опис |
|--------|------|
| `linkify_mentions` | Перетворює @username у клікабельні посилання на профіль. |

*Примітка: у проєкті використовується JS linkify в base.html (mention_filters не підвантажується на деяких хостингах).*

---

## 🔵 main/views.py

| View | URL | Опис |
|------|-----|------|
| **AboutUsView** | `/about/` | Сторінка "Про нас". |

---

## 📋 URL-префікси

- **/profile/** — profiles (логін, профіль, follow, repost, API)
- **/** — posts, main (головна, пошук, пости, коментарі)
- **/admin/** — Django admin

---

## ⚙️ Важливі константи

- `MAX_REPORTS = 2` — після 2 скарг пост видаляється
- `MAX_COMMENT_REPORTS = 3` — після 3 скарг коментар видаляється
- `REACTION_WEIGHTS`: based=+4, toxic=-2, cringe=-5 — вплив на reputation
