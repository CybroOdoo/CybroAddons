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
class TestPurchaseOrderLine(AccountTestInvoicingCommon):

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

    def test_order_line_image_is_related_to_product_image(self):
        self.assertEqual(self.purchase_order.order_line.order_line_image, self.product_image)
