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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#############################################################################
import re

from odoo.tests import HttpCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestRepairControllers(HttpCase):
    """Test cases for the portal and review controllers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = new_test_user(
            cls.env, login='repair_portal_a', groups='base.group_portal')
        cls.other_user = new_test_user(
            cls.env, login='repair_portal_b', groups='base.group_portal')
        cls.repair = cls.env['machine.repair'].create({
            'name': 'Portal Repair',
            'customer_id': cls.portal_user.partner_id.id,
            'priority': 'normal',
            'repair_detail': 'Portal repair detail',
        })
        cls.other_repair = cls.env['machine.repair'].create({
            'name': 'Other Repair',
            'customer_id': cls.other_user.partner_id.id,
            'priority': 'normal',
            'repair_detail': 'Other repair detail',
        })

    def _get_csrf_token(self):
        """Read a CSRF token from the rendered review form."""
        response = self.url_open('/review')
        match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
        self.assertTrue(match, "CSRF token not found in the review form.")
        return match.group(1)

    def test_01_portal_list_shows_own_repairs(self):
        """The portal list page is reachable for a portal user."""
        self.authenticate('repair_portal_a', 'repair_portal_a')
        response = self.url_open('/my/repair')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.repair.repair_seq, response.text)
        self.assertNotIn(self.other_repair.repair_seq, response.text)

    def test_02_portal_detail_own_repair(self):
        """A customer can open the detail page of their own repair."""
        self.authenticate('repair_portal_a', 'repair_portal_a')
        response = self.url_open('/my/repair/%s' % self.repair.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Repair Details', response.text)

    def test_03_portal_detail_other_repair_redirects(self):
        """A customer cannot open the repair of another customer."""
        self.authenticate('repair_portal_a', 'repair_portal_a')
        response = self.url_open('/my/repair/%s' % self.other_repair.id,
                                 allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers['Location'].endswith('/my'))

    def test_04_portal_detail_with_access_token(self):
        """The detail page can be opened with a valid access token."""
        token = self.repair._portal_ensure_token()
        response = self.url_open(
            '/my/repair/%s?access_token=%s' % (self.repair.id, token))
        self.assertEqual(response.status_code, 200)

    def test_05_portal_detail_public_without_token(self):
        """An anonymous visitor without a token is redirected."""
        response = self.url_open('/my/repair/%s' % self.repair.id,
                                 allow_redirects=False)
        self.assertEqual(response.status_code, 303)

    def test_06_review_saves_rating_for_current_customer(self):
        """The review is saved on the repair of the logged-in customer."""
        self.authenticate('repair_portal_a', 'repair_portal_a')
        self.url_open('/create/repair_reviews', data={
            'csrf_token': self._get_csrf_token(),
            'rating': 'excellent',
            'repair_review_comment': 'Great work',
        })
        self.assertEqual(self.repair.customer_rating, 'Excellent')
        self.assertEqual(self.repair.customer_comments, 'Great work')
        self.assertFalse(self.other_repair.customer_rating)

    def test_07_review_ignores_unknown_rating(self):
        """An unknown rating value does not change the repair."""
        self.authenticate('repair_portal_a', 'repair_portal_a')
        self.url_open('/create/repair_reviews', data={
            'csrf_token': self._get_csrf_token(),
            'rating': 'unknown',
            'repair_review_comment': 'Ignored',
        })
        self.assertFalse(self.repair.customer_rating)

    def test_08_review_requires_csrf_token(self):
        """The review route rejects a POST without a CSRF token."""
        self.authenticate('repair_portal_a', 'repair_portal_a')
        response = self.url_open('/create/repair_reviews', data={
            'rating': 'good',
            'repair_review_comment': 'No token',
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.repair.customer_rating)

    def test_09_review_requires_login(self):
        """An anonymous visitor cannot submit a review."""
        self.url_open('/create/repair_reviews', data={
            'csrf_token': self._get_csrf_token(),
            'rating': 'good',
            'repair_review_comment': 'Anonymous',
        })
        self.assertFalse(self.repair.customer_rating)

    def _repair_form_data(self, **extra):
        """Return the values posted by the website repair form."""
        data = {
            'csrf_token': self._get_csrf_token(),
            'customer_id': 'Website Visitor',
            'customer_email': 'visitor@example.com',
            'phone': '123456',
            'repairing_reason': 'Not starting',
            'machine_brand': 'Brand',
            'machine_model': 'Model X',
            'manufacturing_year': '2020-01-01',
            'priority': 'high',
            'repair_detail': 'Machine does not start',
        }
        data.update(extra)
        return data

    def test_10_repair_request_public_creates_partner(self):
        """A public visitor gets a new partner and a repair request."""
        self.url_open('/create/repair_request', data=self._repair_form_data())
        repair = self.env['machine.repair'].search(
            [('customer_id.name', '=', 'Website Visitor')])
        self.assertEqual(len(repair), 1)
        self.assertEqual(repair.customer_id.email, 'visitor@example.com')
        self.assertEqual(repair.priority, 'high')

    def test_11_repair_request_logged_in_uses_own_partner(self):
        """A logged-in customer's request is linked to their own partner."""
        self.authenticate('repair_portal_a', 'repair_portal_a')
        partners_before = self.env['res.partner'].search_count([])
        self.url_open('/create/repair_request', data=self._repair_form_data())
        repair = self.env['machine.repair'].search([
            ('customer_id', '=', self.portal_user.partner_id.id),
            ('name', '=', 'Repair from Website'),
        ])
        self.assertEqual(len(repair), 1)
        self.assertEqual(self.env['res.partner'].search_count([]),
                         partners_before)

    def test_12_repair_request_ignores_unknown_fields(self):
        """Fields that are not part of the form cannot be set."""
        self.url_open('/create/repair_request', data=self._repair_form_data(
            customer_id='Field Tester', state='closed',
            customer_rating='Excellent'))
        repair = self.env['machine.repair'].search(
            [('customer_id.name', '=', 'Field Tester')])
        self.assertEqual(repair.state, 'new')
        self.assertFalse(repair.customer_rating)

    def test_13_repair_request_requires_csrf_token(self):
        """The repair request route rejects a POST without a CSRF token."""
        data = self._repair_form_data(customer_id='No Token')
        data.pop('csrf_token')
        response = self.url_open('/create/repair_request', data=data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.env['machine.repair'].search(
            [('customer_id.name', '=', 'No Token')]))
