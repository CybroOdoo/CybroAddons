# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestPurchaseOrderReport(TransactionCase):

    def test_purchase_order_report_values(self):
        """Test report values retrieval from abstract model."""
        report_model = self.env['report.all_in_one_purchase_kit.purchase_order_report']
        
        # Test calling without context
        res_no_ctx = report_model._get_report_values([], data={})
        self.assertIsNone(res_no_ctx)
        
        # Test calling with context and data
        data = {
            'report_data': {
                'report_lines': ['line1', 'line2'],
                'filters': {'date': '2026-06-22'},
            }
        }
        res_ctx = report_model.with_context(purchase_order_report=True)._get_report_values([], data=data)
        self.assertEqual(res_ctx['report_main_line_data'], ['line1', 'line2'])
        self.assertEqual(res_ctx['Filters'], {'date': '2026-06-22'})
        self.assertEqual(res_ctx['company'], self.env.company)
