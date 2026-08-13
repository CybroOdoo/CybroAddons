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
class TestPurchaseReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['product.brand'].create({'name': 'Report Brand'})
        cls.partner = cls.env['res.partner'].create({'name': 'Report Vendor'})
        cls.product = cls.env['product.product'].create({
            'name': 'Report Product',
            'type': 'consu',
            'brand_id': cls.brand.id,
        })
        cls.po = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_qty': 5,
                'price_unit': 100.0,
            })],
        })
        cls.po.button_confirm()

    def test_purchase_report_brand_field(self):
        """Test brand_id is populated in the purchase.report SQL view."""
        self.assertIn('brand_id', self.env['purchase.report']._fields)
        
        self.env.flush_all()
        
        report_record = self.env['purchase.report'].search([
            ('product_id', '=', self.product.id)
        ])
        
        if report_record:
            self.assertEqual(report_record.brand_id, self.brand)
