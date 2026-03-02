import os

DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS').split()
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF').split()

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

VERCEL_BLOB_TOKEN = os.getenv("VERCEL_BLOB_TOKEN")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': int(os.getenv('DB_PORT', 5432)),
    }
}