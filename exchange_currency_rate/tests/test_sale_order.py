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


@tagged('exchange_currency_rate', 'sale_order')
class TestSaleOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.company_currency = cls.company.currency_id

        cls.customer = cls.env['res.partner'].create({'name': 'Test Customer'})

        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'service',
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
            'list_price': 100.0,
        })

        # Find a foreign currency (any active currency ≠ company currency)
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
            'partner_id': self.customer.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        }
        if currency:
            pricelist = self.env['product.pricelist'].search([('currency_id', '=', currency.id)], limit=1)
            if not pricelist:
                pricelist = self.env['product.pricelist'].create({
                    'name': f'Pricelist {currency.name}',
                    'currency_id': currency.id,
                })
            vals['pricelist_id'] = pricelist.id
            vals['currency_id'] = currency.id
        order = self.env['sale.order'].create(vals)
        # Write is_exchange / rate after create so the constraint fires with
        # fully-resolved company_currency_id and currency_id fields.
        if is_exchange or rate != 1.0:
            order.write({'is_exchange': is_exchange, 'rate': rate})
        return order

    # ==================================================================
    # A. Field tests
    # ==================================================================

    def test_company_currency_id_field_exists(self):
        """company_currency_id Many2one field must exist on sale.order."""
        self.assertIn('company_currency_id', self.env['sale.order']._fields)


    def test_is_exchange_field_exists(self):
        """is_exchange Boolean field must exist on sale.order."""
        self.assertIn('is_exchange', self.env['sale.order']._fields)

    def test_is_exchange_defaults_false(self):
        """is_exchange must default to False."""
        order = self._make_order()
        self.assertFalse(order.is_exchange)

    def test_rate_defaults_to_one(self):
        """rate must default to 1."""
        order = self._make_order()
        self.assertEqual(order.rate, 1.0)

    def test_company_currency_id_mirrors_company(self):
        """company_currency_id must equal company_id.currency_id (related)."""
        order = self._make_order()
        self.assertEqual(order.company_currency_id, self.company.currency_id)

    # ==================================================================
    # B. _onchange_different_currency() constraint
    # ==================================================================

    def test_constraint_disables_is_exchange_when_currency_reverts(self):
        """
        When currency_id is changed back to the company currency,
        the constraint must set is_exchange = False.
        """
        order = self._make_order(
            currency=self.foreign_currency,
            is_exchange=True,
        )
        self.assertTrue(order.is_exchange)
        # Revert to company currency, then manually trigger constraint logic
        # (@api.constrains side-effects are not guaranteed to persist in Odoo 19)
        order.write({'currency_id': self.company_currency.id})
        order._onchange_different_currency()
        self.assertFalse(
            order.is_exchange,
            "is_exchange must be False when currency reverts to company currency",
        )

    def test_constraint_no_effect_when_foreign_currency_kept(self):
        """
        Setting a foreign currency while is_exchange=True must NOT disable it.
        The constraint only acts when currency == company_currency.
        """
        order = self._make_order(currency=self.foreign_currency)
        order.write({'is_exchange': True})
        # Calling the constraint with a foreign currency must leave is_exchange untouched
        order._onchange_different_currency()
        self.assertTrue(
            order.is_exchange,
            "is_exchange must remain True when a foreign currency is kept",
        )

    def test_constraint_noop_when_is_exchange_already_false(self):
        """
        Reverting currency when is_exchange is already False must not crash
        and is_exchange stays False.
        """
        order = self._make_order(
            currency=self.foreign_currency,
            is_exchange=False,
        )
        order.write({'currency_id': self.company_currency.id})  # must not raise
        order._onchange_different_currency()
        self.assertFalse(order.is_exchange)

    # ==================================================================
    # C. _onchange_is_exchange()
    # ==================================================================

    def test_onchange_is_exchange_populates_rate(self):
        """
        Calling _onchange_is_exchange() when is_exchange=True and a foreign
        currency is set must populate rate with a positive value.
        """
        order = self._make_order(currency=self.foreign_currency)
        order.is_exchange = True
        order._onchange_is_exchange()
        self.assertGreater(
            order.rate, 0,
            "rate must be > 0 after _onchange_is_exchange with foreign currency",
        )

    def test_onchange_is_exchange_false_does_not_change_rate(self):
        """
        Calling _onchange_is_exchange() when is_exchange=False must not
        change rate (onchange body is guarded by `if self.is_exchange`).
        """
        order = self._make_order(currency=self.foreign_currency, rate=3.5)
        order.is_exchange = False
        order._onchange_is_exchange()
        self.assertEqual(order.rate, 3.5, "rate must not be changed when is_exchange=False")

    def test_onchange_rate_matches_conversion_rate(self):
        """
        After _onchange_is_exchange(), rate must equal what
        _get_conversion_rate() would return for the same pair/date.
        """
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

    # ==================================================================
    # D. rate field behaviour
    # ==================================================================

    def test_rate_can_be_set_manually(self):
        """rate can be written to any positive float."""
        order = self._make_order()
        order.write({'rate': 4.2567})
        self.assertAlmostEqual(order.rate, 4.2567, places=4)

    def test_rate_zero_is_allowed(self):
        """No constraint prevents rate=0 (field has no python constraint)."""
        order = self._make_order()
        order.write({'rate': 0.0})   # must not raise
        self.assertEqual(order.rate, 0.0)

    def test_is_exchange_and_rate_stored_after_confirm(self):
        """is_exchange and rate are persisted after order confirmation."""
        order = self._make_order(
            currency=self.foreign_currency,
            is_exchange=True,
            rate=2.5,
        )
        order.action_confirm()
        self.assertTrue(order.is_exchange)
        self.assertAlmostEqual(order.rate, 2.5, places=4)
