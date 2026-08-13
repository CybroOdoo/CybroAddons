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
class TestDynamicPurchaseReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Vendor Dynamic Test'})
        cls.product = cls.env['product.product'].create({
            'name': 'Dynamic Test Product',
            'type': 'consu',
        })
        cls.po = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_qty': 5,
                'price_unit': 100.0,
            })],
        })

    def test_dynamic_report_methods(self):
        """Test dynamic purchase report options and SQL fetching."""
        report = self.env['dynamic.purchase.report'].create({
            'report_type': 'report_by_order',
        })
        
        # Test options & translations
        filters = report.get_filter([report.id])
        self.assertEqual(filters['report_type'], 'Report By Order')
        
        filter_data = report.get_filter_data([report.id])
        self.assertEqual(filter_data['report_type'], 'report_by_order')
        
        # Test purchase_report method
        res = report.purchase_report([report.id])
        self.assertEqual(res['name'], "Purchase Orders")
        self.assertTrue('report_lines' in res)
        
        # Test different report types to cover SQL query generation
        for report_type in ['report_by_order', 'report_by_order_detail', 'report_by_product', 'report_by_categories', 'report_by_purchase_representative', 'report_by_state']:
            report.report_type = report_type
            data = {
                'report_type': report_type,
                'model': report,
            }
            res_val = report._get_report_values(data)
            self.assertIn('PURCHASE', res_val)
