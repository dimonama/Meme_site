from Scripts.bottle import response
from django.test import  TestCase

class TestMeme(TestCase):
    def test_gallery(self):
        response = self.client.get('/gallery/')
        self.assertEqual(response.status_code, 200)

    def test_profile(self):
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 302)
    def test_edit(self):
        response = self.client.get('/profile/edit/')
        self.assertEqual(response.status_code, 302)
    def test_upload(self):
        response = self.client.get('/upload/')
        self.assertEqual(response.status_code, 302)
    def test_menu(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)
    def test_login(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
    def test_regiser(self):
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)

