# -*- coding: utf-8 -*-
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestPortalController(HttpCase):

    def setUp(self):
        super().setUp()
        self.portal_user = self.env['res.users'].create({
            'name': 'Portal Client',
            'login': 'portal_client_user',
            'password': 'portal_client_pass',
        })
        self.category = self.env['case.category'].create({
            'name': 'Portal Category'
        })
        self.case = self.env['case.registration'].create({
            'client_id': self.portal_user.partner_id.id,
            'case_category_id': self.category.id,
            'description': 'Portal Case',
        })

    def test_prepare_home_portal_values(self):
        """Test _prepare_home_portal_values is injected correctly"""
        self.authenticate('portal_client_user', 'portal_client_pass')
        response = self.url_open('/my')
        self.assertEqual(response.status_code, 200)

    def test_legal_cases(self):
        """Test GET /my/legal/case route"""
        self.authenticate('portal_client_user', 'portal_client_pass')
        response = self.url_open('/my/legal/case')
        self.assertEqual(response.status_code, 200)

    def test_portal_my_details_detail(self):
        """Test GET /my/cases/<int:case_id> route"""
        self.authenticate('portal_client_user', 'portal_client_pass')
        response = self.url_open(f'/my/cases/{self.case.id}')
        self.assertEqual(response.status_code, 200)
