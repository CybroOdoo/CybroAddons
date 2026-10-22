# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import logging
from lxml import html
from odoo.tests.common import HttpCase, tagged, new_test_user

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestOdooQueueManagerController(HttpCase):
    """Http test cases for Odoo Queue Manager controller routes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Department = cls.env['queue.department']
        cls.QueueCounter = cls.env['queue.counter']
        cls.TokenToken = cls.env['token.token']
        cls.QueueProcess = cls.env['queue.process']

        cls.user_admin = cls.env.ref('base.user_admin')
        cls.user_portal = new_test_user(cls.env, 'portal_user_test', groups='base.group_portal')

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
            _logger.warning("Failed to extract CSRF token from response")
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

        # Non-existent department
        res = self.url_open('/create/token', data={
            'csrf_token': csrf_token,
            'name': 'Test User',
            'department': '9999999',
            'mobile': '123456789'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('Selected department is invalid.', res.text)

        # Missing mobile
        res = self.url_open('/create/token', data={
            'csrf_token': csrf_token,
            'name': 'Test User',
            'department': str(self.dept.id),
            'mobile': ''
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('Please enter a mobile number.', res.text)

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

    def test_create_token_sequential_numbering(self):
        """Test that successive tokens in a department increment monotonically."""
        csrf_token = self._get_csrf_token()

        dept = self.Department.create({'name': 'Finance', 'code': 'FN'})
        res1 = self.url_open('/create/token', data={
            'csrf_token': csrf_token,
            'name': 'Customer One',
            'department': str(dept.id),
            'mobile': '+1234567891'
        })
        self.assertEqual(res1.status_code, 200)
        t1 = self.TokenToken.search([('department_id', '=', dept.id)], order='id desc', limit=1)

        res2 = self.url_open('/create/token', data={
            'csrf_token': csrf_token,
            'name': 'Customer Two',
            'department': str(dept.id),
            'mobile': '+1234567892'
        })
        self.assertEqual(res2.status_code, 200)
        t2 = self.TokenToken.search([('department_id', '=', dept.id)], order='id desc', limit=1)

        self.assertEqual(int(t2.token), int(t1.token) + 1)

    def test_queue_display_screen_route(self):
        """Test GET /queue/display/<counter_id>."""
        res = self.url_open(f'/queue/display/{self.counter.id}')
        self.assertEqual(res.status_code, 200)

    def test_queue_display_screen_fallback_department(self):
        """Test GET /queue/display/<counter_id> when no token is in progress but counter has history."""
        self.TokenToken.create({
            'customer_name': 'Past User',
            'department_id': self.dept.id,
            'counter_id': self.counter.id,
            'state': 'done'
        })
        res = self.url_open(f'/queue/display/{self.counter.id}')
        self.assertEqual(res.status_code, 200)

    def test_public_print_receipt_route(self):
        """Test GET /action/print/<token_id> enforces access_token for public users."""
        token = self.TokenToken.create({
            'customer_name': 'Kiosk User',
            'department_id': self.dept.id,
            'mobile': '1234567890',
            'state': 'draft'
        })
        # Missing access token -> 403 Forbidden
        res_no_token = self.url_open(f'/action/print/{token.id}')
        self.assertEqual(res_no_token.status_code, 403)

        # Wrong access token -> 403 Forbidden
        res_wrong_token = self.url_open(f'/action/print/{token.id}?access_token=wrong123')
        self.assertEqual(res_wrong_token.status_code, 403)

        # Valid access token -> 200 or 302
        res_valid = self.url_open(f'/action/print/{token.id}?access_token={token.access_token}')
        self.assertIn(res_valid.status_code, [200, 302])

        # Authenticated queue user can access without access token
        self.authenticate(self.user_admin.login, self.user_admin.login)
        res_admin = self.url_open(f'/action/print/{token.id}')
        self.assertIn(res_admin.status_code, [200, 302])

    def test_portal_user_forbidden_on_queue_routes(self):
        """Verify that portal users cannot access queue counter and processing routes."""
        self.authenticate('portal_user_test', 'portal_user_test')

        # Counter processing
        res = self.url_open(f'/queue/counter/{self.dept.id}/{self.counter.id}')
        self.assertEqual(res.status_code, 403)

        # Empty token
        res = self.url_open('/empty/token')
        self.assertEqual(res.status_code, 403)

        # Process individual token
        token = self.TokenToken.create({
            'customer_name': 'Portal Token Test',
            'department_id': self.dept.id,
            'state': 'draft'
        })
        res = self.url_open(f'/process/individual/token/{token.id}/{self.counter.id}')
        self.assertEqual(res.status_code, 403)

        # Queue submit
        csrf_token = self._get_csrf_token()
        res = self.url_open(
            f'/queue/submit/{token.id}/{self.counter.id}',
            data={
                'csrf_token': csrf_token,
                'token_state': 'done'
            }
        )
        self.assertEqual(res.status_code, 403)

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
        self.assertEqual(token.user_id, self.user_admin)

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
        self.assertEqual(token.user_id, self.user_admin)

        qp = self.QueueProcess.search([
            ('customer_name', '=', 'Queue User')
        ], limit=1)
        self.assertTrue(qp.exists())
        self.assertEqual(qp.customer_query, 'Query test')

    def test_individual_queue_processing_transitions_previous_token(self):
        """Test starting a new token marks previously in_progress token as done."""
        self.authenticate(self.user_admin.login, self.user_admin.login)

        token1 = self.TokenToken.create({
            'customer_name': 'First Customer',
            'department_id': self.dept.id,
            'counter_id': self.counter.id,
            'state': 'in_progress'
        })
        token2 = self.TokenToken.create({
            'customer_name': 'Second Customer',
            'department_id': self.dept.id,
            'state': 'draft'
        })

        res = self.url_open(
            f'/process/individual/token/{token2.id}/{self.counter.id}'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(token1.state, 'done')
        self.assertEqual(token2.state, 'in_progress')

    def test_individual_queue_processing_non_existent_token(self):
        """Test /process/individual/token with invalid token renders empty queue page."""
        self.authenticate(self.user_admin.login, self.user_admin.login)

        res = self.url_open(f'/process/individual/token/9999999/{self.counter.id}')
        self.assertEqual(res.status_code, 200)

    def test_queue_submit_recall_and_cancelled(self):
        """Test submitting token states 'recall' and 'cancelled'."""
        self.authenticate(self.user_admin.login, self.user_admin.login)

        # Recall submission
        token_recall = self.TokenToken.create({
            'customer_name': 'Recall User',
            'department_id': self.dept.id,
            'counter_id': self.counter.id,
            'state': 'in_progress'
        })
        res = self.url_open(f'/process/individual/token/{token_recall.id}/{self.counter.id}')
        csrf_token = self._extract_csrf_token(res)

        res_recall = self.url_open(
            f'/queue/submit/{token_recall.id}/{self.counter.id}',
            data={
                'csrf_token': csrf_token,
                'token_state': 'recall',
            }
        )
        self.assertEqual(res_recall.status_code, 200)
        self.assertEqual(token_recall.state, 'recall')

        # Cancelled submission
        token_cancelled = self.TokenToken.create({
            'customer_name': 'Cancelled User',
            'department_id': self.dept.id,
            'counter_id': self.counter.id,
            'state': 'in_progress'
        })
        res_cancel = self.url_open(
            f'/queue/submit/{token_cancelled.id}/{self.counter.id}',
            data={
                'csrf_token': csrf_token,
                'token_state': 'cancelled',
            }
        )
        self.assertEqual(res_cancel.status_code, 200)
        self.assertEqual(token_cancelled.state, 'cancelled')

    def test_queue_submit_non_existent_token(self):
        """Test submitting non-existent token redirects to /empty/token."""
        self.authenticate(self.user_admin.login, self.user_admin.login)

        csrf_token = self._get_csrf_token()

        res = self.url_open(
            f'/queue/submit/9999999/{self.counter.id}',
            data={
                'csrf_token': csrf_token,
                'token_state': 'done',
            }
        )
        self.assertEqual(res.status_code, 200)
