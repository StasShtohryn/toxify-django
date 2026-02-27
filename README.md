# toxify-django
A Django-powered social network inspired by Twitter — built for hot takes, fast discussions, and chaotic community energy.

<div align="center">
  <img src="https://kfsim1lapad8t68g.public.blob.vercel-storage.com/toxify.jpg" width="1024" alt="Toxify Image">
</div>

## Virtual Environment

Create a virtual environment:
```console
python -m venv venv
```
Activate the virtual environment:
- Linux:
```console
source venv/bin/activate
```
- Windows:
```console
venv/Scripts/activate
```

## Install packages
Django:
```console
pip install django
```
Django-Split-Settings:
```console
pip install django-split-settings
```
Django-Widget-Tweaks:
```console
pip install django-widget-tweaks
```
Pillow:
```console
pip install pillow
```
Python-Dotenv:
```console
pip install python-dotenv
```

## Configuration

Create ```.env``` file next to ```manage.py``` in ```Toxify/``` folder with the following variables:
```env
DEBUG=True
SECRET_KEY='YOUR_DJANGO_SECRET_KEY'
```
