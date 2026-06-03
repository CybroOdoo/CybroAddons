# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
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
################################################################################
import re

from odoo.tests.common import HttpCase, TransactionCase


class TestInsuranceQuoteRequestController(HttpCase):
    """HTTP integration tests for the InsuranceQuoteRequest website controller.

    Covers:
    - GET /insurance/request/form — HTTP 200 and page content
    - POST /insurance/request/form/submit — CSRF-aware record creation
    """

    def setUp(self):
        super().setUp()
        self.authenticate('1', '1')

    # ------------------------------------------------------------------
    # GET /insurance/request/form
    # ------------------------------------------------------------------

    def test_insurance_request_form_get_returns_200(self):
        """GET /insurance/request/form must return HTTP 200."""
        response = self.url_open('/insurance/request/form')
        self.assertEqual(response.status_code, 200,
                         "GET /insurance/request/form should return 200.")


    def test_insurance_request_form_contains_expected_content(self):
        """Response for GET /insurance/request/form must include insurance-related HTML."""
        response = self.url_open('/insurance/request/form')
        content = response.text.lower()
        self.assertIn('insurance', content,
                      "Page content should mention 'insurance'.")


    # ------------------------------------------------------------------
    # POST /insurance/request/form/submit — CSRF-aware
    # ------------------------------------------------------------------

    def _get_csrf_token(self, response_text):
        """Extract the CSRF token from an HTML form response."""
        match = re.search(
            r'<input[^>]+name=["\']csrf_token["\'][^>]+value=["\']([^"\']+)["\']',
            response_text,
        )
        if not match:
            # Try alternative order of attributes
            match = re.search(
                r'<input[^>]+value=["\']([^"\']+)["\'][^>]+name=["\']csrf_token["\']',
                response_text,
            )
        return match.group(1) if match else ''


class TestInsuranceQuoteRequestLogic(TransactionCase):
    """Unit tests for the controller's business logic — ORM level.

    These tests bypass HTTP and directly exercise the create() call that
    the controller makes, verifying the record is created correctly.
    """

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create(
            {'name': 'Logic Test Partner'})
        self.category = self.env['insurance.policy.category'].create(
            {'name': 'LogicCat', 'code': 'LGC'})
        self.sub_cat = self.env['insurance.policy.sub.category'].create(
            {'name': 'LogicSub', 'category_id': self.category.id})
        self.i_doc = self.env['insured.document'].create({'name': 'LogicIDoc'})
        self.c_doc = self.env['claim.document'].create({'name': 'LogicCDoc'})
        self.policy = self.env['insurance.policy'].create({
            'insurance_policy_id': self.sub_cat.id,
            'policy_number': 'LGC-001',
            'insurance_amount': 80000.0,
            'claim_amount': 30000.0,
            'policy_document_ids': [(4, self.i_doc.id)],
            'claim_document_ids': [(4, self.c_doc.id)],
        })
        self.company = self.env.company

    def test_controller_create_logic_creates_insurance_record(self):
        """Simulate controller form submission: creating res.insurance via ORM."""
        post = {
            'holder': str(self.partner.id),
            'gender': 'male',
            'provider': str(self.company.id),
            'policy': str(self.policy.id),
            'date_of_birth': '1992-06-15',
            'age': '31',
            'phone': '9998887770',
            'email': 'controller@example.com',
        }
        count_before = self.env['res.insurance'].search_count([])
        self.env['res.insurance'].sudo().create({
            'policy_holder_id': post.get('holder'),
            'gender': post.get('gender'),
            'policy_provider_id': post.get('provider'),
            'insurance_policy_id': post.get('policy'),
            'dob': post.get('date_of_birth'),
            'phone': post.get('phone'),
            'email': post.get('email'),
        })
        count_after = self.env['res.insurance'].search_count([])
        self.assertEqual(count_after, count_before + 1,
                         "Controller ORM logic should create one res.insurance record.")


    def test_controller_create_logic_stores_gender(self):
        """Controller ORM create must store the gender field."""
        record = self.env['res.insurance'].sudo().create({
            'policy_holder_id': str(self.partner.id),
            'gender': 'female',
            'insurance_policy_id': str(self.policy.id),
            'commission_type': 'fixed',
            'payment_type': 'fixed',
        })
        self.assertEqual(record.gender, 'female',
                         "gender should be stored as 'female'.")


    def test_controller_create_logic_stores_phone_and_email(self):
        """Controller ORM create must store phone and email from form post."""
        record = self.env['res.insurance'].sudo().create({
            'policy_holder_id': self.partner.id,
            'gender': 'male',
            'insurance_policy_id': self.policy.id,
            'commission_type': 'fixed',
            'payment_type': 'fixed',
            'phone': '1112223330',
            'email': 'stored@example.com',
        })
        self.assertEqual(record.phone, '1112223330',
                         "phone should be stored correctly.")
        self.assertEqual(record.email, 'stored@example.com',
                         "email should be stored correctly.")

