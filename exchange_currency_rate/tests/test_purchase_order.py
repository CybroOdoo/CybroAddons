# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase, tagged


@tagged('exchange_currency_rate', 'purchase_order')
class TestPurchaseOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.company_currency = cls.company.currency_id

        cls.vendor = cls.env['res.partner'].create({'name': 'Test Vendor'})

        cls.product = cls.env['product.product'].create({
            'name': 'Test Purchase Product',
            'type': 'consu',
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
            'standard_price': 50.0,
        })

        cls.foreign_currency = cls.env['res.currency'].search(
            [('id', '!=', cls.company_currency.id), ('active', '=', True)],
            limit=1,
        )
        if not cls.foreign_currency:
            cls.foreign_currency = cls.env['res.currency'].with_context(active_test=False).search(
                [('id', '!=', cls.company_currency.id)], limit=1
            )
            if cls.foreign_currency:
                cls.foreign_currency.write({'active': True})
            else:
                cls.foreign_currency = cls.env['res.currency'].create({
                    'name': 'EUR',
                    'symbol': '€',
                })

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _make_order(self, currency=None, is_exchange=False, rate=1.0):
        vals = {
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 1.0,
                'price_unit': 50.0,
                'date_planned': '2026-01-01',
            })],
        }
        if currency:
            vals['currency_id'] = currency.id
        order = self.env['purchase.order'].create(vals)
        # Write is_exchange / rate after create so the constraint fires with
        # fully-resolved company_currency_id and currency_id fields.
        if is_exchange or rate != 1.0:
            order.write({'is_exchange': is_exchange, 'rate': rate})
        return order

    # ==================================================================
    # A. Field tests
    # ==================================================================

    def test_company_currency_id_field_exists(self):
        """company_currency_id Many2one field must exist on purchase.order."""
        self.assertIn('company_currency_id', self.env['purchase.order']._fields)


    def test_is_exchange_field_exists(self):
        """is_exchange Boolean field must exist on purchase.order."""
        self.assertIn('is_exchange', self.env['purchase.order']._fields)

    def test_is_exchange_defaults_false(self):
        """is_exchange must default to False on a new purchase order."""
        order = self._make_order()
        self.assertFalse(order.is_exchange)

    def test_rate_defaults_to_one(self):
        """rate must default to 1."""
        order = self._make_order()
        self.assertEqual(order.rate, 1.0)

    def test_company_currency_id_mirrors_company(self):
        """company_currency_id must equal company_id.currency_id."""
        order = self._make_order()
        self.assertEqual(order.company_currency_id, self.company.currency_id)

    # ==================================================================
    # B. _onchange_different_currency() constraint
    # ==================================================================

    def test_constraint_disables_is_exchange_on_currency_revert(self):
        """Reverting to company currency must set is_exchange = False."""
        order = self._make_order(currency=self.foreign_currency, is_exchange=True)
        self.assertTrue(order.is_exchange)
        order.write({'currency_id': self.company_currency.id})
        # Manually trigger the constraint logic since @api.constrains side-effects
        # are not guaranteed to persist in Odoo 19
        order._onchange_different_currency()
        self.assertFalse(
            order.is_exchange,
            "is_exchange must be False when currency reverts to company currency",
        )

    def test_constraint_no_effect_with_foreign_currency(self):
        """Keeping a foreign currency must NOT disable is_exchange."""
        order = self._make_order(currency=self.foreign_currency)
        order.write({'is_exchange': True})
        # Calling constraint with a foreign currency must leave is_exchange untouched
        order._onchange_different_currency()
        self.assertTrue(order.is_exchange)

    def test_constraint_noop_when_is_exchange_false(self):
        """Reverting currency when is_exchange=False must not crash."""
        order = self._make_order(currency=self.foreign_currency, is_exchange=False)
        order.write({'currency_id': self.company_currency.id})
        order._onchange_different_currency()
        self.assertFalse(order.is_exchange)

    # ==================================================================
    # C. _onchange_is_exchange()
    # ==================================================================

    def test_onchange_is_exchange_populates_rate(self):
        """
        _onchange_is_exchange() when is_exchange=True must populate
        rate with a positive value from _get_conversion_rate.
        """
        order = self._make_order(currency=self.foreign_currency)
        order.is_exchange = True
        order._onchange_is_exchange()
        self.assertGreater(order.rate, 0)

    def test_onchange_rate_matches_conversion_rate(self):
        """rate set by onchange must match _get_conversion_rate output."""
        order = self._make_order(currency=self.foreign_currency)
        expected = self.env['res.currency']._get_conversion_rate(
            from_currency=order.company_currency_id,
            to_currency=order.currency_id,
            company=order.company_id,
            date=order.date_order,
        )
        order.is_exchange = True
        order._onchange_is_exchange()
        self.assertAlmostEqual(order.rate, expected, places=6)

    def test_onchange_false_does_not_change_rate(self):
        """_onchange_is_exchange() when is_exchange=False must not modify rate."""
        order = self._make_order(currency=self.foreign_currency, rate=7.89)
        order.is_exchange = False
        order._onchange_is_exchange()
        self.assertAlmostEqual(order.rate, 7.89, places=4)

    # ==================================================================
    # D. rate field behaviour
    # ==================================================================

    def test_is_exchange_and_rate_survive_confirmation(self):
        """is_exchange and rate must persist after button_confirm()."""
        order = self._make_order(
            currency=self.foreign_currency,
            is_exchange=True,
            rate=5.0,
        )
        order.button_confirm()
        self.assertTrue(order.is_exchange)
        self.assertAlmostEqual(order.rate, 5.0, places=4)

    # ==================================================================
    # E. Parity with sale.order
    # ==================================================================

    def test_parity_constraint_same_as_sale_order(self):
        """
        purchase.order and sale.order implement the same constraint logic:
        reverting to company currency disables is_exchange in both.
        """
        # Sale order — create without is_exchange, then write it after so the
        # constraint fires with fully-resolved currency fields.
        sale = self.env['sale.order'].create({
            'partner_id': self.vendor.id,
            'currency_id': self.foreign_currency.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 50.0,
            })],
        })
        sale.write({'is_exchange': True})
        # Purchase order
        purchase = self._make_order(currency=self.foreign_currency, is_exchange=True)

        # Revert both to company currency, then trigger constraint logic explicitly
        sale.write({'currency_id': self.company_currency.id})
        sale._onchange_different_currency()
        purchase.write({'currency_id': self.company_currency.id})
        purchase._onchange_different_currency()

        self.assertFalse(sale.is_exchange, "sale.order constraint must disable is_exchange")
        self.assertFalse(purchase.is_exchange, "purchase.order constraint must disable is_exchange")
