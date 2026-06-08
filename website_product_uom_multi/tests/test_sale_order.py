# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.info)
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
################################################################################
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.website_product_uom_multi.models import (
    sale_order as sale_order_module,
)


class FakeRequest:

    def __init__(self, env):
        self.env = env
        self.session = {}


@tagged('post_install', '-at_install')
class TestSaleOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.uom_pack_6 = cls.env.ref('uom.product_uom_pack_6')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Website UoM Customer',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Website UoM Sale Product',
            'type': 'consu',
            'list_price': 10.0,
            'uom_id': cls.uom_unit.id,
        })

    def _create_order(self):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'website_id': self.env['website'].get_current_website().id,
        })

    def test_cart_update_creates_line_with_selected_uom(self):
        order = self._create_order()

        values = order._cart_update(
            product_id=self.product.id,
            add_qty=2,
            uom=self.uom_pack_6.id,
        )
        line = self.env['sale.order.line'].browse(values['line_id'])

        self.assertEqual(values['quantity'], 2)
        self.assertEqual(line.product_uom_id, self.uom_pack_6)

    def test_cart_find_product_line_filters_by_uom(self):
        order = self._create_order()
        unit_line = order._cart_update(
            product_id=self.product.id,
            add_qty=1,
            uom=self.uom_unit.id,
        )
        pack_line = order._cart_update(
            product_id=self.product.id,
            add_qty=1,
            uom=self.uom_pack_6.id,
        )

        unit_lines = order._cart_find_product_line(
            self.product.id, uom_id=self.uom_unit.id
        )
        pack_lines = order._cart_find_product_line(
            self.product.id, uom_id=self.uom_pack_6.id
        )

        self.assertEqual(unit_lines.ids, [unit_line['line_id']])
        self.assertEqual(pack_lines.ids, [pack_line['line_id']])

    def test_cart_update_order_line_updates_uom_and_removes_zero_quantity(self):
        order = self._create_order()
        values = order._cart_update(
            product_id=self.product.id,
            add_qty=1,
            uom=self.uom_unit.id,
        )
        line = self.env['sale.order.line'].browse(values['line_id'])

        updated_line = order._cart_update_order_line(
            line, 3, uom_id=self.uom_pack_6, product_id=self.product.id
        )

        self.assertEqual(updated_line.product_uom_qty, 3)
        self.assertEqual(updated_line.product_uom_id, self.uom_pack_6)

        removed_line = order._cart_update_order_line(updated_line, 0)

        self.assertFalse(removed_line)
        self.assertFalse(updated_line.exists())

    def test_cart_update_rejects_non_draft_order(self):
        order = self._create_order()
        order.action_confirm()

        with self.assertRaises(UserError), \
                patch.object(sale_order_module, 'request', FakeRequest(self.env)):
            order._cart_update(
                product_id=self.product.id,
                add_qty=1,
                uom=self.uom_unit.id,
            )
