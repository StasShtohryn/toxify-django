from split_settings.tools import include
import os


include('base.py')

DEBUG = os.getenv("DEBUG") == 'True'



if DEBUG:
    include('local.py')
else:
    include('prod.py')