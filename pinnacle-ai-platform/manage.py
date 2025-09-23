#!/usr/bin/env python3
"""
Django management script for Pinnacle AI Platform

This script provides Django management commands for database operations,
admin interface, and other Django-specific functionality.
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line


def main():
    """Run Django management commands."""
    # Add the src directory to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(project_root, 'src')
    sys.path.insert(0, src_dir)

    # Configure Django settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': os.getenv('DB_NAME', 'pinnacle_ai'),
                    'USER': os.getenv('DB_USER', 'pinnacle_user'),
                    'PASSWORD': os.getenv('DB_PASSWORD', 'pinnacle_password'),
                    'HOST': os.getenv('DB_HOST', 'localhost'),
                    'PORT': os.getenv('DB_PORT', '5432'),
                }
            },
            INSTALLED_APPS=[
                'django.contrib.admin',
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.messages',
                'django.contrib.staticfiles',
                'rest_framework',
                'corsheaders',
                # Add your apps here
                'core.auth',
                'core.database',
                'services.ecommerce',
                'services.agents',
            ],
            MIDDLEWARE=[
                'django.middleware.security.SecurityMiddleware',
                'django.contrib.sessions.middleware.SessionMiddleware',
                'corsheaders.middleware.CorsMiddleware',
                'django.middleware.common.CommonMiddleware',
                'django.middleware.csrf.CsrfViewMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware',
                'django.middleware.clickjacking.XFrameOptionsMiddleware',
            ],
            SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
            USE_TZ=True,
            USE_I18N=True,
            USE_L10N=True,
            ROOT_URLCONF='core.urls',
            TEMPLATES=[
                {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': [os.path.join(project_root, 'templates')],
                    'APP_DIRS': True,
                    'OPTIONS': {
                        'context_processors': [
                            'django.template.context_processors.debug',
                            'django.template.context_processors.request',
                            'django.contrib.auth.context_processors.auth',
                            'django.contrib.messages.context_processors.messages',
                        ],
                    },
                },
            ],
            STATIC_URL='/static/',
            STATIC_ROOT=os.path.join(project_root, 'staticfiles'),
            MEDIA_URL='/media/',
            MEDIA_ROOT=os.path.join(project_root, 'media'),
            CORS_ALLOWED_ORIGINS=[
                "http://localhost:3000",
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000",
            ],
            REST_FRAMEWORK={
                'DEFAULT_PERMISSION_CLASSES': [
                    'rest_framework.permissions.IsAuthenticated',
                ],
                'DEFAULT_AUTHENTICATION_CLASSES': [
                    'rest_framework.authentication.SessionAuthentication',
                    'rest_framework.authentication.BasicAuthentication',
                ],
                'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
                'PAGE_SIZE': 20,
            },
        )

    # Setup Django
    django.setup()

    # Execute Django management command
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()