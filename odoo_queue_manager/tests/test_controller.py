# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from lxml import html
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestOdooQueueManagerController(HttpCase):
    """Http test cases for Odoo Queue Manager controller routes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Department = cls.env['department']
        cls.QueueCounter = cls.env['queue.counter']
        cls.TokenToken = cls.env['token.token']
        cls.QueueProcess = cls.env['queue.process']

        cls.user_admin = cls.env.ref('base.user_admin')

        cls.dept = cls.Department.create({
            'name': 'IT Support',
            'code': 'IT'
        })
        cls.counter = cls.QueueCounter.create({
            'name': 'Counter IT'
        })

    def _extract_csrf_token(self, res):
        """Extract CSRF token from HTTP response HTML."""
        try:
            tree = html.fromstring(res.content)
            tokens = tree.xpath('//input[@name="csrf_token"]/@value')
            if tokens:
                return tokens[0]
        except Exception:
            pass
        return ''

    def _get_csrf_token(self):
        """Fetch CSRF token from generate token page."""
        res = self.url_open('/generate/token')
        return self._extract_csrf_token(res)

    def test_generate_token_route(self):
        """Test GET /generate/token endpoint returns 200 OK."""
        res = self.url_open('/generate/token')
        self.assertEqual(res.status_code, 200)

    def test_create_token_validation_failures(self):
        """Test POST /create/token validations (missing name, department, mobile)."""
        csrf_token = self._get_csrf_token()

        # Missing name
        res = self.url_open('/create/token', data={
            'csrf_token': csrf_token,
            'name': '',
            'department': str(self.dept.id),
            'mobile': '123456789'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('Please enter your name.', res.text)

        # Missing department
        res = self.url_open('/create/token', data={
            'csrf_token': csrf_token,
            'name': 'Test User',
            'department': '',
            'mobile': '123456789'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('Please select a department.', res.text)

        # Invalid mobile
        res = self.url_open('/create/token', data={
            'csrf_token': csrf_token,
            'name': 'Test User',
            'department': str(self.dept.id),
            'mobile': 'invalid_phone'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('Please enter a valid phone number.', res.text)

    def test_create_token_success(self):
        """Test successful token creation via POST /create/token."""
        csrf_token = self._get_csrf_token()

        res = self.url_open('/create/token', data={
            'csrf_token': csrf_token,
            'name': 'Valid User',
            'department': str(self.dept.id),
            'mobile': '+1234567890'
        })
        self.assertEqual(res.status_code, 200)

        token = self.TokenToken.search([
            ('customer_name', '=', 'Valid User'),
            ('department_id', '=', self.dept.id)
        ], limit=1)
        self.assertTrue(token.exists())
        self.assertEqual(token.mobile, '+1234567890')

    def test_queue_display_screen_route(self):
        """Test GET /queue/display/<counter_id>."""
        res = self.url_open(f'/queue/display/{self.counter.id}')
        self.assertEqual(res.status_code, 200)

    def test_authenticated_routes(self):
        """Test authenticated endpoints after logging in."""
        self.authenticate(self.user_admin.login, self.user_admin.login)

        # Counter processing page
        res = self.url_open(f'/queue/counter/{self.dept.id}/{self.counter.id}')
        self.assertEqual(res.status_code, 200)

        # Empty token page
        res = self.url_open('/empty/token')
        self.assertEqual(res.status_code, 200)

        # Individual token processing
        token = self.TokenToken.create({
            'customer_name': 'Queue User',
            'department_id': self.dept.id,
            'mobile': '1234567890',
            'state': 'draft'
        })
        res = self.url_open(
            f'/process/individual/token/{token.id}/{self.counter.id}'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(token.state, 'in_progress')

        # Extract CSRF token from the individual processing response HTML tree
        csrf_token = self._extract_csrf_token(res)

        # Queue submit - Done state
        res = self.url_open(
            f'/queue/submit/{token.id}/{self.counter.id}',
            data={
                'csrf_token': csrf_token,
                'token_state': 'done',
                'customer_query': 'Query test',
                'feedback': 'Feedback test'
            }
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(token.state, 'done')

        qp = self.QueueProcess.search([
            ('customer_name', '=', 'Queue User')
        ], limit=1)
        self.assertTrue(qp.exists())
        self.assertEqual(qp.customer_query, 'Query test')
