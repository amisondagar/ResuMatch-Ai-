"""
test_app.py — Verification suite for ResumeMatch.ai
"""

import os
import tempfile
import unittest
import uuid
from app import create_app

class TestResumeMatch(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['DATABASE_PATH'] = self.db_path
        
        # Init test DB
        with self.app.app_context():
            from services.db_service import init_db
            init_db()

        self.client = self.app.test_client()

    def tearDown(self):
        try:
            os.close(self.db_fd)
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except Exception:
            pass

    def test_01_landing_page(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'ResumeMatch', res.data)

    def test_02_register_login_and_full_flow(self):
        # Register
        res = self.client.post('/auth/register', data={
            'username': 'recruiter123',
            'email': 'recruiter123@example.com',
            'full_name': 'Test Recruiter',
            'company': 'Tech Corp',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Dashboard', res.data)

        # Logout
        res = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Login
        res = self.client.post('/auth/login', data={
            'email': 'recruiter123@example.com',
            'password': 'Password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Dashboard', res.data)

        # Check all protected pages
        routes = [
            '/dashboard/',
            '/dashboard/notifications',
            '/dashboard/profile',
            '/resume/upload',
            '/resume/list',
            '/jd/create',
            '/jd/list',
            '/analysis/run',
            '/analysis/ranking',
            '/analytics/',
            '/reports/'
        ]
        for route in routes:
            r = self.client.get(route, follow_redirects=True)
            self.assertEqual(r.status_code, 200, f"Route {route} failed with status {r.status_code}")

        # Create JD
        res = self.client.post('/jd/create', data={
            'title': 'Senior Python Developer',
            'company': 'Acme AI',
            'description': 'We are looking for a Senior Python Developer with Flask, SQL, Docker, and REST API experience.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Verify JD list
        res = self.client.get('/jd/list')
        self.assertIn(b'Senior Python Developer', res.data)

        # Upload Resume
        resume_content = b"""
        John Doe
        john.doe@example.com | (555) 123-4567 | San Francisco, CA

        SUMMARY:
        Senior Python Engineer with 6 years of experience building scalable microservices and Web APIs.

        SKILLS:
        Python, Flask, Django, PostgreSQL, Docker, Git, REST API, Linux, SQL, Microservices, Machine Learning

        EXPERIENCE:
        Senior Software Engineer - Tech Solutions Inc. (2020 - Present)
        - Developed high performance Python microservices using Flask and PostgreSQL.

        EDUCATION:
        Bachelor of Science in Computer Science - State University
        """

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(resume_content)
            tmp_path = tmp.name

        try:
            with open(tmp_path, 'rb') as f:
                res = self.client.post('/resume/upload', data={
                    'resumes': (f, 'john_doe_resume.pdf')
                }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'John Doe', res.data)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == '__main__':
    unittest.main()
