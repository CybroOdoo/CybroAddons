# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author:  Ayana KP (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests import TransactionCase


class TestSaleOrderReport(TransactionCase):

    def setUp(self):
        super(TestSaleOrderReport, self).setUp()
        self.report_model = self.env['report.sale_report_generator.sale_order_report']
        
    def test_get_report_values(self):
        """Test that _get_report_values correctly merges data when context sale_order_report is set"""
        # Call without context
        data = {'test': 'value'}
        res = self.report_model._get_report_values([], data.copy())
        # Should be none because the method only returns data if context is set or no super is called
        # Wait, the method doesn't call super() and returns data directly if context is set, but if context is not set, it implicitly returns None
        self.assertEqual(res, None)

        # Call with context
        data = {
            'report_data': {
                'report_lines': ['line1', 'line2'],
                'filters': {'date_from': '2023-01-01'}
            }
        }
        res = self.report_model.with_context(sale_order_report=True)._get_report_values([], data.copy())
        self.assertIn('report_main_line_data', res)
        self.assertEqual(res['report_main_line_data'], ['line1', 'line2'])
        self.assertIn('Filters', res)
        self.assertEqual(res['Filters'], {'date_from': '2023-01-01'})
        self.assertIn('company', res)
        self.assertEqual(res['company'], self.env.company)
