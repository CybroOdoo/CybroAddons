# -*- coding: utf-8 -*-
from unittest.mock import patch
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestLegalCaseManagementController(HttpCase):
    """
    Test cases for the Legal Case Management Controller (portal actions).
    """

    def setUp(self):
        super().setUp()
        self.test_user = self.env['res.users'].create({
            'name': 'Controller Test User',
            'login': 'controller_test_user',
            'password': 'controller_test_pass',
        })
        self.category = self.env['case.category'].create({'name': 'Test Category'})

    def test_legal_case_register(self):
        """Test GET /legal/case/register route"""
        self.authenticate('controller_test_user', 'controller_test_pass')
        response = self.url_open('/legal/case/register')
        self.assertEqual(response.status_code, 200)

    def test_create_case_register(self):
        """
        Test the case register POST route
        """
        self.authenticate('controller_test_user', 'controller_test_pass')
        
        with patch('odoo.http.Request.validate_csrf', return_value=True):
            response = self.url_open(
                '/submit/create/case',
                data={
                    'description': 'Test case from controller',
                    'case_category': self.category.id,
                    'contact': '1234567890',
                }
            )
        self.assertEqual(response.status_code, 200)

        case = self.env['case.registration'].search([
            ('description', 'ilike', 'Test case from controller')
        ])
        self.assertTrue(case)
        self.assertEqual(case.contact_no, '1234567890')
        self.assertEqual(case.case_category_id.id, self.category.id)
        self.assertEqual(case.client_id.id, self.test_user.partner_id.id)
