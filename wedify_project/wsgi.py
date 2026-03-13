"""
WSGI config for wedify_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys
import traceback

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wedify_project.settings')

try:
    application = get_wsgi_application()
    app = application
except Exception as e:
    print(f"WSGI LOAD ERROR: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    raise
