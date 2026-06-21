# -*- coding: utf-8 -*-

import json
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestLegalCaseDashboard(HttpCase):
    """
    Test cases for legal_case_management_dashboard controller.
    Covers: get_legal_case_dashboard_values, add_lawyer_selection_field,
            date_filter, fetch_dashboard_without_filter_value,
            fetch_dashboard_filter_value
    """

    def setUp(self):
        super().setUp()
        self.test_user = self.env['res.users'].create({
            'name': 'Dashboard Test User',
            'login': 'dashboard_test_user',
            'password': 'dashboard_test_pass',
        })
        lawyer_group = self.env.ref(
            'legal_case_management.legal_case_management_group_lawyer')
        self.test_user.write({
            'group_ids': [(4, lawyer_group.id)]
        })
        # Create an hr.employee linked to the test user so the dashboard
        # controller's search([('employee_id.user_id', '=', uid)]) finds
        # a record and has_group() does not raise ensure_one() ValueError.
        self.env['hr.employee'].create({
            'name': 'Dashboard Test User',
            'user_id': self.test_user.id,
            'is_lawyer': True,
        })
        self.company_id = self.env.company.id

    def _json_post(self, url, params=None):
        """Helper to perform JSON-RPC POST requests."""
        payload = json.dumps({
            'jsonrpc': '2.0',
            'method': 'call',
            'params': params or {},
            'id': 1,
        })
        response = self.url_open(
            url,
            data=payload,
            headers={'Content-Type': 'application/json'},
        )
        return response

    def test_get_legal_case_dashboard_values(self):
        """
        Test /case/dashboard route returns 200 and a valid JSON result
        with all expected keys.
        """
        self.authenticate('dashboard_test_user', 'dashboard_test_pass')
        response = self._json_post(
            '/case/dashboard',
            params={'current_company_id': self.company_id}
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('result', body)
        result = body['result']
        # Verify all required keys are present in the dashboard payload
        expected_keys = [
            'total_case', 'invoices', 'total_invoiced', 'lawyers',
            'lawyer_ids', 'evidences', 'trials', 'clients',
            'clients_in_case', 'case_category', 'data_list',
            'stage_count', 'invoice_list', 'top_10_cases',
            'user_id', 'lawyer_object',
        ]
        for key in expected_keys:
            self.assertIn(key, result,
                          f"Expected key '{key}' not found in dashboard result")

    def test_get_legal_case_dashboard_values_stage_count(self):
        """
        Test /case/dashboard returns stage_count with all 7 predefined stages.
        """
        self.authenticate('dashboard_test_user', 'dashboard_test_pass')
        response = self._json_post(
            '/case/dashboard',
            params={'current_company_id': self.company_id}
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        stage_count = body['result']['stage_count']
        # First row is header ['Stage', 'Cases']
        self.assertEqual(stage_count[0], ['Stage', 'Cases'])
        stage_names = [row[0] for row in stage_count[1:]]
        expected_stages = ['Draft', 'In Progress', 'Invoiced', 'Reject',
                           'Won', 'Lost', 'Cancel']
        for stage in expected_stages:
            self.assertIn(stage, stage_names,
                          f"Stage '{stage}' missing from stage_count data")

    def test_get_legal_case_dashboard_values_monthly_data(self):
        """
        Test /case/dashboard monthly_income_data has header and 13 entries.
        """
        self.authenticate('dashboard_test_user', 'dashboard_test_pass')
        response = self._json_post(
            '/case/dashboard',
            params={'current_company_id': self.company_id}
        )
        self.assertEqual(response.status_code, 200)
        data_list = response.json()['result']['data_list']
        # Header row + 13 monthly entries (range 0..12)
        self.assertEqual(data_list[0], ['Month', 'Income'])
        self.assertEqual(len(data_list), 14)

    def test_add_lawyer_selection_field(self):
        """
        Test /selection/field/lawyer returns 200 and a list result.
        Each item should have 'name' and 'id' keys.
        """
        self.authenticate('dashboard_test_user', 'dashboard_test_pass')
        response = self._json_post('/selection/field/lawyer')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('result', body)
        result = body['result']
        self.assertIsInstance(result, list)
        for lawyer in result:
            self.assertIn('name', lawyer)
            self.assertIn('id', lawyer)

    def test_date_filter(self):
        """
        Test the date_filter helper method returns all required date keys.
        """
        from odoo.addons.legal_case_management_dashboard.controllers.\
            legal_case_management_dashboard import LegalCaseDashboard
        controller = LegalCaseDashboard()
        result = controller.date_filter()
        expected_keys = [
            'first_day_of_last_month',
            'last_day_of_last_month',
            'first_day_of_six_months_ago',
            'first_day_of_twelve_months_ago',
        ]
        for key in expected_keys:
            self.assertIn(key, result,
                          f"Expected date key '{key}' missing from date_filter result")
        # first_day_of_last_month must be <= last_day_of_last_month
        self.assertLessEqual(
            result['first_day_of_last_month'],
            result['last_day_of_last_month']
        )
        # six months start must be before twelve months start
        self.assertGreater(
            result['first_day_of_six_months_ago'],
            result['first_day_of_twelve_months_ago']
        )

    def test_fetch_dashboard_without_filter_value(self):
        """
        Test /dashboard/without/filter returns 200 and all required keys.
        """
        self.authenticate('dashboard_test_user', 'dashboard_test_pass')
        response = self._json_post(
            '/dashboard/without/filter',
            params={'current_company_id': self.company_id}
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('result', body)
        result = body['result']
        expected_keys = ['total_case', 'total_invoiced', 'lawyers',
                         'evidences', 'trials', 'clients']
        for key in expected_keys:
            self.assertIn(key, result,
                          f"Expected key '{key}' missing from filter result")
        # Counts must be non-negative integers or floats
        self.assertGreaterEqual(result['total_case'], 0)
        self.assertGreaterEqual(result['total_invoiced'], 0)
        self.assertGreaterEqual(result['lawyers'], 0)

    def test_fetch_dashboard_filter_value_admin_no_stage(self):
        """
        Test /dashboard/filter with lawyer='admin' and no stage filter.
        Expects 200 and result with all required keys.
        """
        self.authenticate('dashboard_test_user', 'dashboard_test_pass')
        response = self._json_post(
            '/dashboard/filter',
            params={
                'data': {
                    'lawyer': 'admin',
                    'stage': None,
                }
            }
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('result', body)
        result = body['result']
        expected_keys = ['total_case', 'total_invoiced', 'lawyers',
                         'evidences', 'trials', 'clients']
        for key in expected_keys:
            self.assertIn(key, result)
        self.assertIsInstance(result['total_case'], list)
        self.assertGreaterEqual(result['total_invoiced'], 0)

    def test_fetch_dashboard_filter_value_admin_with_stage(self):
        """
        Test /dashboard/filter with lawyer='admin' and a specific stage.
        """
        self.authenticate('dashboard_test_user', 'dashboard_test_pass')
        for stage in ['draft', 'in_progress', 'won', 'lost', 'invoiced',
                      'cancel']:
            response = self._json_post(
                '/dashboard/filter',
                params={
                    'data': {
                        'lawyer': 'admin',
                        'stage': stage,
                    }
                }
            )
            self.assertEqual(response.status_code, 200,
                             f"Failed for stage '{stage}'")
            result = response.json().get('result', {})
            self.assertIn('total_case', result)

    def test_fetch_dashboard_filter_value_month_wise_last_month(self):
        """
        Test /dashboard/filter with month_wise='last_month' filter.
        """
        self.authenticate('dashboard_test_user', 'dashboard_test_pass')
        response = self._json_post(
            '/dashboard/filter',
            params={
                'data': {
                    'lawyer': 'admin',
                    'stage': None,
                    'month_wise': 'last_month',
                }
            }
        )
        self.assertEqual(response.status_code, 200)
        result = response.json().get('result', {})
        self.assertIn('total_case', result)
        self.assertIsInstance(result['total_case'], list)

    def test_fetch_dashboard_filter_value_month_wise_last_6_months(self):
        """
        Test /dashboard/filter with month_wise='last_6_months' filter.
        """
        self.authenticate('dashboard_test_user', 'dashboard_test_pass')
        response = self._json_post(
            '/dashboard/filter',
            params={
                'data': {
                    'lawyer': 'admin',
                    'stage': None,
                    'month_wise': 'last_6_months',
                }
            }
        )
        self.assertEqual(response.status_code, 200)
        result = response.json().get('result', {})
        self.assertIn('total_case', result)

    def test_fetch_dashboard_filter_value_month_wise_last_12_months(self):
        """
        Test /dashboard/filter with month_wise='last_12_months' filter.
        """
        self.authenticate('dashboard_test_user', 'dashboard_test_pass')
        response = self._json_post(
            '/dashboard/filter',
            params={
                'data': {
                    'lawyer': 'admin',
                    'stage': None,
                    'month_wise': 'last_12_months',
                }
            }
        )
        self.assertEqual(response.status_code, 200)
        result = response.json().get('result', {})
        self.assertIn('total_case', result)
