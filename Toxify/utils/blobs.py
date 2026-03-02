import requests
import os

url = "https://ogulkughunqoppwg.public.blob.vercel-storage.com/"

def upload_to_vercel_blob(file):
    token = os.getenv("VERCEL_BLOB_TOKEN")
    filename = file.name

    url = f"https://blob.vercel-storage.com/{filename}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": file.content_type,
    }

    response = requests.put(
        url,
        headers=headers,
        data=file.read(),
    )

    if response.status_code not in (200, 201):
        raise Exception(f"Upload failed: {response.text}")

    return response.json()["url"]