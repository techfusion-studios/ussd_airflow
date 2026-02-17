from django.core.management import call_command
import json
import os
import sys
from django.urls import re_path, include
from django.test import TestCase
from django.conf import settings
from django.core.management import call_command
from django.test.utils import override_settings
import shutil

from ussd_airflow import urls
from rest_framework.test import APIClient


class TestUssdAppIsNotCreated(TestCase):

    def test_app_not_created(self):
        app_name = 'TestUssdApp TestUssdApp'
        call_command('create_ussd_app', app_name)
        with self.assertRaises(ImportError):
            include(app_name)


class TestUssdAppCreation(TestCase):

    def setUp(self):
        self.app_name = 'TestUssdApp'
        call_command('create_ussd_app', self.app_name)
        self.app_path = os.path.join(settings.BASE_DIR, self.app_name)

    def tearDown(self):
        # Clean up created app directory
        if os.path.exists(self.app_path):
            shutil.rmtree(self.app_path)
        # Remove the app path from sys.path
        if os.path.abspath(self.app_path) in sys.path:
            sys.path.remove(os.path.abspath(self.app_path))

    def test_app_files_created(self):
        # Verify that the app directory and key files exist
        self.assertTrue(os.path.exists(self.app_path))
        self.assertTrue(os.path.exists(os.path.join(self.app_path, 'views.py')))
        self.assertTrue(os.path.exists(os.path.join(self.app_path, 'urls.py')))
        self.assertTrue(os.path.exists(os.path.join(self.app_path, 'customer_journey.yml')))

        # Optionally, check content of views.py and urls.py to ensure correct templating
        with open(os.path.join(self.app_path, 'views.py'), 'r') as f:
            content = f.read()
            self.assertIn(f'class TestussdappView(UssdView):', content)
            self.assertIn(f'customer_journey_namespace = "TestussdappUssdGateWay"', content)
        
        with open(os.path.join(self.app_path, 'urls.py'), 'r') as f:
            content = f.read()
            self.assertIn(f"from .views import TestussdappView", content)
            self.assertIn(f"re_path(r'', TestussdappView.as_view()),", content)


