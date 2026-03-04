import requests
import os

url = "https://ogulkughunqoppwg.public.blob.vercel-storage.com/"


def upload_to_vercel_blob(file, folder: str = "misc") -> str:
    """
    folder — підпапка в Vercel Blob: 'avatars', 'posts', 'comments'
    """
    token = os.getenv("VERCEL_BLOB_TOKEN")
    filename = file.name

    # Структура: posts/filename.jpg, avatars/filename.jpg
    path = f"{folder}/{filename}"

    url = f"https://blob.vercel-storage.com/{path}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": file.content_type,
    }

    response = requests.put(url, headers=headers, data=file.read())

    if response.status_code not in (200, 201):
        raise Exception(f"Upload failed: {response.text}")

    return response.json()["url"]



def delete_from_vercel_blob(url: str) -> None:
    """
    Видаляє файл з Vercel Blob за його URL.
    Не видаляє дефолтний аватар.
    """
    if not url:
        return

    # Не видаляємо дефолтний аватар
    if 'default.jpg' in url:
        return

    token = os.getenv("VERCEL_BLOB_TOKEN")
    if not token:
        return

    try:
        response = requests.delete(
            "https://blob.vercel-storage.com",
            headers={"Authorization": f"Bearer {token}"},
            json={"urls": [url]},
        )
        if response.status_code not in (200, 204):
            print(f"Vercel Blob delete failed: {response.text}")
    except Exception as e:
        print(f"Vercel Blob delete error: {e}")
