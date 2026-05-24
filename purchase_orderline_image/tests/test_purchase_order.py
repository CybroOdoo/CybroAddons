# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
import base64

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('-at_install', 'post_install')
class TestPurchaseOrder(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_image = base64.b64encode(b'purchase-order-line-image')
        cls.product_a.image_128 = cls.product_image
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner_a.id,
            'order_line': [(0, 0, {
                'product_id': cls.product_a.id,
                'name': cls.product_a.display_name,
                'product_qty': 2.0,
                'price_unit': 50.0,
                'date_planned': '2026-05-08 00:00:00',
            })],
        })

    def test_purchase_order_computes_show_image_flag_disabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'purchase_orderline_image.show_product_image_in_report_purchase', False
        )

        self.purchase_order.invalidate_recordset(['show_product_image_setting'])
        self.purchase_order._compute_show_product_image_setting()

        self.assertFalse(self.purchase_order.show_product_image_setting)

    def test_purchase_order_computes_show_image_flag_enabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'purchase_orderline_image.show_product_image_in_report_purchase', True
        )

        self.purchase_order.invalidate_recordset(['show_product_image_setting'])
        self.purchase_order._compute_show_product_image_setting()

        self.assertTrue(self.purchase_order.show_product_image_setting)

    def test_purchase_order_report_hides_image_column_when_disabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'purchase_orderline_image.show_product_image_in_report_purchase', False
        )

        html = self.env['ir.actions.report']._render_qweb_html(
            'purchase.report_purchaseorder', self.purchase_order.ids
        )[0].decode('utf-8')

        self.assertNotIn('<strong>Image</strong>', html)

    def test_purchase_order_report_shows_image_column_when_enabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'purchase_orderline_image.show_product_image_in_report_purchase', True
        )

        html = self.env['ir.actions.report']._render_qweb_html(
            'purchase.report_purchaseorder', self.purchase_order.ids
        )[0].decode('utf-8')

        self.assertIn('<strong>Image</strong>', html)
        self.assertIn('data:image/png;base64,', html)
