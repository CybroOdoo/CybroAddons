# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

###############################################################################
from odoo.tests.common import TransactionCase

class TestPurchaseOrderReport(TransactionCase):

    def setUp(self):
        super().setUp()

        self.report_model = self.env['report.all_in_one_purchase_kit.purchase_order_report']

    def test_get_report_values(self):
        """Test report values generation with context."""
        data = {
            'report_data': {
                'report_lines': ['line1'],
                'filters': {'date': 'today'}
            }
        }
        
        # Should return None without context
        result_no_ctx = self.report_model._get_report_values([], data.copy())
        self.assertIsNone(result_no_ctx)
        
        # With context
        result_ctx = self.report_model.with_context(purchase_order_report=True)._get_report_values([], data.copy())
        self.assertIn('report_main_line_data', result_ctx)
        self.assertEqual(result_ctx['report_main_line_data'], ['line1'])
        self.assertIn('Filters', result_ctx)
        self.assertIn('company', result_ctx)
