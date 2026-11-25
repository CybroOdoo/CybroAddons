# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arshad Ali Pottengal (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestDamageDetail(common.TransactionCase):
    """Test suite for the damage.detail model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product = cls.env['product.product'].create({
            'name': 'Damage Test Product',
            'type': 'consu',
            'lst_price': 200.0,
        })

    # ------------------------------------------------------------------
    # _onchange_product_id
    # ------------------------------------------------------------------

    def test_onchange_product_id_sets_price_and_quantity(self):
        """Changing product sets unit_price to lst_price and quantity to 1."""
        damage = self.env['damage.detail'].new({
            'product_id': self.product.id,
            'quantity': 5,
            'unit_price': 0.0,
        })
        damage._onchange_product_id()
        self.assertEqual(damage.unit_price, self.product.lst_price)
        self.assertEqual(damage.quantity, 1)

    def test_onchange_product_id_no_product(self):
        """With no product set, onchange should not raise."""
        damage = self.env['damage.detail'].new({})
        damage._onchange_product_id()
        # unit_price defaults to 0 (lst_price of empty Many2one is 0)
        self.assertEqual(damage.unit_price, 0.0)

    # ------------------------------------------------------------------
    # _compute_subtotal
    # ------------------------------------------------------------------

    def test_quantity_change_keeps_unit_price(self):
        """Changing quantity keeps the unit price and updates the subtotal."""
        damage = self.env['damage.detail'].new({
            'product_id': self.product.id,
            'unit_price': self.product.lst_price,
            'quantity': 3,
        })
        self.assertEqual(damage.unit_price, self.product.lst_price)
        self.assertAlmostEqual(damage.subtotal, self.product.lst_price * 3)

    def test_compute_subtotal(self):
        """Subtotal is unit price multiplied by quantity and follows edits."""
        damage = self.env['damage.detail'].create({
            'product_id': self.product.id,
            'unit_price': 200.0,
            'quantity': 2,
        })
        self.assertAlmostEqual(damage.subtotal, 400.0)
        damage.quantity = 0
        self.assertEqual(damage.subtotal, 0.0)

    # ------------------------------------------------------------------
    # Create / basic field checks
    # ------------------------------------------------------------------

    def test_create_damage_detail(self):
        """A damage.detail record can be created and retrieved correctly."""
        damage = self.env['damage.detail'].create({
            'product_id': self.product.id,
            'unit_price': 200.0,
            'quantity': 2,
            'expense_note': 'Cracked screen',
        })
        self.assertTrue(damage.id)
        self.assertEqual(damage.product_id, self.product)
        self.assertEqual(damage.quantity, 2)
        self.assertEqual(damage.expense_note, 'Cracked screen')

    def test_damage_detail_default_quantity(self):
        """Default quantity for a new damage.detail is 1."""
        damage = self.env['damage.detail'].create({
            'product_id': self.product.id,
        })
        self.assertEqual(damage.quantity, 1)
