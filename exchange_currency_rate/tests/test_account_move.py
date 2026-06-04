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

@tagged('exchange_currency_rate', 'account_move')
class TestAccountMove(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.company_currency = cls.company.currency_id

        cls.customer = cls.env['res.partner'].create(
            {'name': 'Test Customer AM', 'customer_rank': 1}
        )
        cls.vendor = cls.env['res.partner'].create(
            {'name': 'Test Vendor AM', 'supplier_rank': 1}
        )

        cls.product = cls.env['product.product'].create({
            'name': 'AM Test Product',
            'type': 'service',
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
            'list_price': 100.0,
            'standard_price': 100.0,
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

        # ── Accounting setup (Odoo 19: no company_id on account.account) ──
        cls.sale_journal = cls.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1
        )
        cls.purchase_journal = cls.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1
        )
        cls.revenue_account = cls.env['account.account'].search(
            [('account_type', '=', 'income')], limit=1
        )
        cls.expense_account = cls.env['account.account'].search(
            [('account_type', '=', 'expense')], limit=1
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_sale_order(self, is_exchange=False, rate=1.0, currency=None):
        """Confirmed sale order with one line."""
        vals = {
            'partner_id': self.customer.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        }
        if currency:
            vals['currency_id'] = currency.id
        so = self.env['sale.order'].create(vals)
        # Write is_exchange / rate after create so the constraint fires with
        # fully-resolved company_currency_id and currency_id fields.
        if is_exchange or rate != 1.0:
            so.write({'is_exchange': is_exchange, 'rate': rate})
        so.action_confirm()
        return so

    def _make_purchase_order(self, is_exchange=False, rate=1.0, currency=None):
        """Confirmed purchase order with one line."""
        vals = {
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 1.0,
                'price_unit': 100.0,
                'date_planned': '2026-01-01',
            })],
        }
        if currency:
            vals['currency_id'] = currency.id
        po = self.env['purchase.order'].create(vals)
        # Write is_exchange / rate after create so the constraint fires with
        # fully-resolved company_currency_id and currency_id fields.
        if is_exchange or rate != 1.0:
            po.write({'is_exchange': is_exchange, 'rate': rate})
        po.button_confirm()
        return po

    def _invoice_from_sale(self, so):
        """Create and return the invoice generated from a sale order."""
        so._create_invoices()
        invoice = self.env['account.move'].search(
            [('invoice_origin', '=', so.name),
             ('move_type', '=', 'out_invoice')],
            limit=1,
        )
        return invoice

    def _invoice_from_purchase(self, po):
        """Create and return a vendor bill linked to a purchase order."""
        action = po.action_create_invoice()
        invoice = self.env['account.move'].browse(action.get('res_id'))
        return invoice

    def _make_standalone_invoice(self, currency=None, is_exchange=False, rate=1.0):
        """Minimal standalone customer invoice (not linked to any SO/PO)."""
        vals = {
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'journal_id': self.sale_journal.id,
            'invoice_line_ids': [(0, 0, {
                'display_type': 'product',
                'name': 'Test Line',
                'quantity': 1.0,
                'price_unit': 100.0,
                'account_id': self.revenue_account.id,
            })],
        }
        if currency:
            vals['currency_id'] = currency.id
        invoice = self.env['account.move'].create(vals)
        if is_exchange:
            invoice.write({'is_exchange': is_exchange, 'rate': rate})
        return invoice

    # ==================================================================
    # A. Field existence & types
    # ==================================================================

    def test_is_exchange_field_exists(self):
        """is_exchange field must exist on account.move, and it's a BOOLEAN field."""
        self.assertIn('is_exchange', self.env['account.move']._fields)
        from odoo.fields import Boolean
        self.assertIsInstance(self.env['account.move']._fields['is_exchange'], Boolean)

    def test_rate_field_exists(self):
        """rate field must exist on account.move and rate must be a Float field"""
        self.assertIn('rate', self.env['account.move']._fields)
        from odoo.fields import Float
        self.assertIsInstance(self.env['account.move']._fields['rate'], Float)


    def test_sale_order_id_field_exists(self):
        """sale_order_id field must exist on account.move."""
        self.assertIn('sale_order_id', self.env['account.move']._fields)

    def test_purchase_order_id_field_exists(self):
        """purchase_order_id field must exist on account.move."""
        self.assertIn('purchase_order_id', self.env['account.move']._fields)

    # ==================================================================
    # B. _compute_sale_order_id
    # ==================================================================

    def test_sale_order_id_populated_from_so(self):
        """Invoice created via SO must have sale_order_id set."""
        so = self._make_sale_order()
        invoice = self._invoice_from_sale(so)
        if not invoice:
            self.skipTest("Could not create invoice from SO — check sale module config")
        invoice.invalidate_recordset(['sale_order_id'])
        self.assertEqual(
            invoice.sale_order_id, so,
            "sale_order_id must point to the originating sale order",
        )

    def test_sale_order_id_false_on_standalone_invoice(self):
        """Standalone invoice (no SO lines) must have sale_order_id = False."""
        invoice = self._make_standalone_invoice()
        self.assertFalse(invoice.sale_order_id)

    # ==================================================================
    # C. _compute_purchase_order_id
    # ==================================================================

    def test_purchase_order_id_populated_from_po(self):
        """Vendor bill created via PO must have purchase_order_id set."""
        po = self._make_purchase_order()
        invoice = self._invoice_from_purchase(po)
        if not invoice:
            self.skipTest("Could not create bill from PO")
        invoice.invalidate_recordset(['purchase_order_id'])
        self.assertEqual(invoice.purchase_order_id, po)

    def test_purchase_order_id_false_on_standalone_invoice(self):
        """Standalone invoice must have purchase_order_id = False."""
        invoice = self._make_standalone_invoice()
        self.assertFalse(invoice.purchase_order_id)

    # ==================================================================
    # D. _compute_is_exchange
    # ==================================================================

    def test_is_exchange_inherited_from_sale_order(self):
        """Invoice must inherit is_exchange=True from the linked SO."""
        so = self._make_sale_order(
            is_exchange=True,
            rate=3.0,
            currency=self.foreign_currency,
        )
        invoice = self._invoice_from_sale(so)
        if not invoice:
            self.skipTest("Could not create invoice from SO")
        invoice.invalidate_recordset(['is_exchange'])
        self.assertTrue(invoice.is_exchange)

    def test_is_exchange_inherited_from_purchase_order(self):
        """Vendor bill must inherit is_exchange=True from the linked PO."""
        po = self._make_purchase_order(
            is_exchange=True,
            rate=2.5,
            currency=self.foreign_currency,
        )
        invoice = self._invoice_from_purchase(po)
        if not invoice:
            self.skipTest("Could not create bill from PO")
        invoice.invalidate_recordset(['is_exchange'])
        self.assertTrue(invoice.is_exchange)

    def test_is_exchange_false_on_standalone(self):
        """Standalone invoice with no SO/PO must have is_exchange=False."""
        invoice = self._make_standalone_invoice()
        self.assertFalse(invoice.is_exchange)

    # ==================================================================
    # E. _compute_rate
    # ==================================================================

    def test_rate_inherited_from_sale_order(self):
        """Invoice rate must equal the linked SO's rate."""
        so = self._make_sale_order(
            is_exchange=True,
            rate=6.123,
            currency=self.foreign_currency,
        )
        invoice = self._invoice_from_sale(so)
        if not invoice:
            self.skipTest("Could not create invoice from SO")
        invoice.invalidate_recordset(['rate'])
        self.assertAlmostEqual(invoice.rate, 6.123, places=3)

    def test_rate_inherited_from_purchase_order(self):
        """Vendor bill rate must equal the linked PO's rate."""
        po = self._make_purchase_order(
            is_exchange=True,
            rate=2.789,
            currency=self.foreign_currency,
        )
        invoice = self._invoice_from_purchase(po)
        if not invoice:
            self.skipTest("Could not create bill from PO")
        invoice.invalidate_recordset(['rate'])
        self.assertAlmostEqual(invoice.rate, 2.789, places=3)

    # ==================================================================
    # F. _compute_invoice_currency_rate (override)
    # ==================================================================

    def test_invoice_currency_rate_uses_manual_rate_when_is_exchange(self):
        """
        When is_exchange=True, invoice_currency_rate must equal move.rate.
        """
        manual_rate = 8.5
        invoice = self._make_standalone_invoice(
            currency=self.foreign_currency,
            is_exchange=True,
            rate=manual_rate,
        )
        invoice.invalidate_recordset(['invoice_currency_rate'])
        self.assertAlmostEqual(invoice.invoice_currency_rate, manual_rate, places=4)

    def test_invoice_currency_rate_falls_back_to_one_when_rate_zero(self):
        """
        When is_exchange=True but rate=0, invoice_currency_rate must be 1
        (the fallback `rate if rate else 1` in the override).
        """
        invoice = self._make_standalone_invoice(
            currency=self.foreign_currency,
            is_exchange=True,
            rate=0.0,
        )
        invoice.invalidate_recordset(['invoice_currency_rate'])
        self.assertAlmostEqual(invoice.invoice_currency_rate, 1.0, places=4)

    def test_invoice_currency_rate_uses_standard_when_not_exchange(self):
        """
        When is_exchange=False, invoice_currency_rate must come from
        the standard _get_conversion_rate, not the manual rate field.
        """
        invoice = self._make_standalone_invoice(
            currency=self.foreign_currency,
            is_exchange=False,
        )
        expected = self.env['res.currency']._get_conversion_rate(
            from_currency=invoice.company_currency_id,
            to_currency=invoice.currency_id,
            company=invoice.company_id,
            date=invoice._get_invoice_currency_rate_date(),
        )
        invoice.invalidate_recordset(['invoice_currency_rate'])
        self.assertAlmostEqual(invoice.invoice_currency_rate, expected, places=6)

    # ==================================================================
    # G. _onchange_different_currency constraint
    # ==================================================================

    def test_constraint_disables_is_exchange_on_currency_revert(self):
        """Reverting invoice currency to company currency disables is_exchange."""
        invoice = self._make_standalone_invoice(
            currency=self.foreign_currency,
            is_exchange=True,
            rate=3.0,
        )
        # Write currency back to company currency, then manually trigger
        # the constraint logic (constraints are validators in Odoo 19 and
        # cannot reliably persist side-effect field writes on their own)
        invoice.write({'currency_id': self.company_currency.id})
        invoice._onchange_different_currency()
        self.assertFalse(
            invoice.is_exchange,
            "is_exchange must be False when invoice currency = company currency",
        )

    def test_constraint_no_effect_with_foreign_currency(self):
        """Keeping a foreign currency must not disable is_exchange."""
        invoice = self._make_standalone_invoice(
            currency=self.foreign_currency,
        )
        invoice.write({'is_exchange': True})
        # Constraint must leave is_exchange untouched when currency is foreign
        invoice._onchange_different_currency()
        self.assertTrue(
            invoice.is_exchange,
            "is_exchange must remain True when a foreign currency is set",
        )