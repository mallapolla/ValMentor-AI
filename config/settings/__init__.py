import os
from dotenv import load_dotenv

load_dotenv()

env = os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.development')
