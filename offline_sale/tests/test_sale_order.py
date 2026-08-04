# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'offline_sale')
class TestPrepareOfflinePartnerVals(TransactionCase):
    """Tests for SaleOrder._prepare_offline_partner_vals."""

    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env['sale.order']

    def test_prepare_vals_all_fields(self):
        """All provided fields are correctly mapped to partner vals."""
        data = {
            'name': 'Alice',
            'street': '123 Main St',
            'city': 'Springfield',
            'zip': '12345',
            'phone': '555-1234',
            'email': 'alice@example.com',
            'website': 'https://alice.com',
            'vat': 'US123456',
            'mobile': '555-9999',
        }
        vals = self.SaleOrder._prepare_offline_partner_vals(data)
        self.assertEqual(vals['name'], 'Alice')
        self.assertEqual(vals['street'], '123 Main St')
        self.assertEqual(vals['city'], 'Springfield')
        self.assertEqual(vals['zip'], '12345')
        self.assertEqual(vals['phone'], '555-1234')
        self.assertEqual(vals['email'], 'alice@example.com')
        self.assertEqual(vals['website'], 'https://alice.com')
        self.assertEqual(vals['vat'], 'US123456')

    def test_prepare_vals_partner_name_fallback(self):
        """'partner_name' is used when 'name' is absent."""
        data = {'partner_name': 'Bob'}
        vals = self.SaleOrder._prepare_offline_partner_vals(data)
        self.assertEqual(vals['name'], 'Bob')

    def test_prepare_vals_default_name(self):
        """'Offline Customer' default name when no name is provided."""
        vals = self.SaleOrder._prepare_offline_partner_vals({})
        self.assertEqual(vals['name'], 'Offline Customer')

    def test_prepare_vals_empty_strings_for_missing_fields(self):
        """Missing optional fields default to empty strings."""
        vals = self.SaleOrder._prepare_offline_partner_vals({'name': 'Test'})
        self.assertEqual(vals['street'], '')
        self.assertEqual(vals['city'], '')
        self.assertEqual(vals['zip'], '')
        self.assertEqual(vals['phone'], '')
        self.assertEqual(vals['email'], '')


@tagged('post_install', '-at_install', 'offline_sale')
class TestGetOrCreateOfflinePartner(TransactionCase):
    """Tests for SaleOrder._get_or_create_offline_partner."""

    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env['sale.order']

    def test_create_new_partner_when_no_match(self):
        """A new partner is created when no existing match is found."""
        data = {
            'id': 'OFF-TEST-001',
            'name': 'New Offline Partner',
            'email': 'newoffline999@example.com',
        }
        partner = self.SaleOrder._get_or_create_offline_partner('OFF-TEST-001', data)
        self.assertTrue(partner.id)
        self.assertEqual(partner.name, 'New Offline Partner')
        self.assertEqual(partner.email, 'newoffline999@example.com')

    def test_returns_existing_partner_by_email(self):
        """An existing partner is returned when matched by email."""
        existing = self.env['res.partner'].create({
            'name': 'Existing Partner',
            'email': 'exist_offline@example.com',
        })
        data = {
            'id': 'OFF-TEST-002',
            'name': 'Existing Partner',
            'email': 'exist_offline@example.com',
        }
        partner = self.SaleOrder._get_or_create_offline_partner('OFF-TEST-002', data)
        self.assertEqual(partner.id, existing.id,
                         "Should return the existing partner matched by email.")

    def test_returns_existing_partner_by_phone(self):
        """An existing partner is returned when matched by phone."""
        existing = self.env['res.partner'].create({
            'name': 'Phone Partner',
            'phone': '000-PHONE-MATCH',
        })
        data = {
            'id': 'OFF-TEST-003',
            'name': 'Phone Partner',
            'phone': '000-PHONE-MATCH',
        }
        partner = self.SaleOrder._get_or_create_offline_partner('OFF-TEST-003', data)
        self.assertEqual(partner.id, existing.id)

    def test_create_partner_with_minimal_data(self):
        """Partner is created even when only an offline ID is supplied."""
        partner = self.SaleOrder._get_or_create_offline_partner('OFF-MINIMAL')
        self.assertTrue(partner.id)
        self.assertEqual(partner.name, 'Offline Customer')


@tagged('post_install', '-at_install', 'offline_sale')
class TestCreateFromOffline(TransactionCase):
    """Tests for SaleOrder.create_from_offline."""

    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env['sale.order']
        self.product = self.env['product.product'].create({
            'name': 'Offline Test Product',
            'sale_ok': True,
            'lst_price': 100.0,
            'type': 'consu',
            'invoice_policy': 'order',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Offline Test Customer',
            'email': 'offline_customer@test.com',
        })

    def _order_data(self, uid, state='draft', extra=None):
        data = {
            'uid': uid,
            'state': state,
            'partner_id': self.partner.id,
            'lines': [
                {
                    'product_id': self.product.id,
                    'qty': 2,
                    'price_unit': 100.0,
                    'discount': 0,
                }
            ],
        }
        if extra:
            data.update(extra)
        return data

    def test_create_new_draft_order(self):
        """A new draft sale order is created for an unknown offline UID."""
        uid = 'OFF-ORDER-DRAFT-001'
        result = self.SaleOrder.create_from_offline([self._order_data(uid, 'draft')])
        self.assertEqual(len(result['orders']), 1)
        res = result['orders'][0]
        self.assertEqual(res['uid'], uid)
        self.assertEqual(res['status'], 'created')
        order = self.SaleOrder.search([('offline_uid', '=', uid)])
        self.assertTrue(order)
        self.assertEqual(order.state, 'draft')

    def test_create_confirmed_order_with_payment(self):
        """A confirmed order is created and invoice payment attempted."""
        uid = 'OFF-ORDER-CONFIRM-001'
        data = self._order_data(uid, 'confirmed', {'amount_paid': 200.0})
        result = self.SaleOrder.create_from_offline([data])
        res = result['orders'][0]
        self.assertEqual(res['uid'], uid)
        self.assertIn(res['status'], ('created',))
        order = self.SaleOrder.search([('offline_uid', '=', uid)])
        self.assertTrue(order)
        self.assertEqual(order.state, 'sale')

    def test_update_existing_draft_order(self):
        """An existing draft order with the same UID is updated."""
        uid = 'OFF-ORDER-UPDATE-001'
        # First creation
        self.SaleOrder.create_from_offline([self._order_data(uid, 'draft')])
        # Second sync – different qty
        data = self._order_data(uid, 'draft')
        data['lines'][0]['qty'] = 5
        result = self.SaleOrder.create_from_offline([data])
        res = result['orders'][0]
        self.assertEqual(res['status'], 'updated')
        order = self.SaleOrder.search([('offline_uid', '=', uid)])
        self.assertEqual(order.order_line[0].product_uom_qty, 5)

    def test_missing_uid_is_skipped(self):
        """Orders without a uid are silently skipped."""
        result = self.SaleOrder.create_from_offline([{'state': 'draft', 'partner_id': self.partner.id}])
        self.assertEqual(result['orders'], [])

    def test_missing_partner_returns_error(self):
        """Order with no valid partner_id returns an error entry."""
        result = self.SaleOrder.create_from_offline([{
            'uid': 'OFF-NO-PARTNER',
            'state': 'draft',
            'partner_id': None,
            'lines': [],
        }])
        self.assertEqual(result['orders'][0]['status'], 'error')

    def test_offline_partner_creation_via_partners_data(self):
        """Partners supplied in partners_data are created and mapped to orders."""
        uid = 'OFF-ORDER-PMAP-001'
        partners_data = [{
            'id': 'OFF-P-MAP-001',
            'name': 'Mapped Partner',
            'email': 'mapped_partner_offline@test.com',
        }]
        order_data = {
            'uid': uid,
            'state': 'draft',
            'partner_id': 'OFF-P-MAP-001',
            'lines': [{'product_id': self.product.id, 'qty': 1, 'price_unit': 50.0, 'discount': 0}],
        }
        result = self.SaleOrder.create_from_offline([order_data], partners_data=partners_data)
        res = result['orders'][0]
        self.assertEqual(res['status'], 'created')

    def test_backend_order_payment_registration(self):
        """Syncing a backend order registers payment against the existing SO."""
        # Create a real sale order to simulate a backend order
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })
        order.action_confirm()

        uid = 'OFF-BACKEND-001'
        data = {
            'uid': uid,
            'backend_order_id': order.id,
            'state': 'confirmed',
            'partner_id': self.partner.id,
            # Use order.amount_total so payment covers the full invoice
            # regardless of any taxes applied in the test environment.
            'amount_paid': order.amount_total,
            'lines': [],
        }
        result = self.SaleOrder.create_from_offline([data])
        res = result['orders'][0]
        self.assertEqual(res['uid'], uid)
        self.assertEqual(res['status'], 'paid_existing')


@tagged('post_install', '-at_install', 'offline_sale')
class TestPostOfflineBackendNote(TransactionCase):
    """Tests for SaleOrder._post_offline_backend_note."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Note Test Partner'})
        self.order = self.env['sale.order'].create({'partner_id': self.partner.id})

    def test_note_is_posted_to_chatter(self):
        """A non-empty backend note is posted to the order chatter."""
        initial_msg_count = len(self.order.message_ids)
        self.env['sale.order']._post_offline_backend_note(
            self.order, {'backend_note': 'Cash payment collected on site.'}
        )
        self.assertGreater(len(self.order.message_ids), initial_msg_count)

    def test_empty_note_is_not_posted(self):
        """An empty or whitespace-only backend note is not posted."""
        initial_msg_count = len(self.order.message_ids)
        self.env['sale.order']._post_offline_backend_note(self.order, {'backend_note': '   '})
        self.assertEqual(len(self.order.message_ids), initial_msg_count)

    def test_missing_note_key_does_not_raise(self):
        """Missing 'backend_note' key does not raise an exception."""
        try:
            self.env['sale.order']._post_offline_backend_note(self.order, {})
        except Exception as e:
            self.fail("_post_offline_backend_note raised unexpectedly: %s" % e)


@tagged('post_install', '-at_install', 'offline_sale')
class TestCreateOfflineInvoiceFromOrderedQty(TransactionCase):
    """Tests for SaleOrder._create_offline_invoice_from_ordered_qty."""

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Invoice Qty Product',
            'type': 'consu',
            'invoice_policy': 'order',
            'lst_price': 50.0,
        })
        self.partner = self.env['res.partner'].create({'name': 'Invoice Partner'})
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 3,
                'price_unit': 50.0,
            })],
        })
        self.order.action_confirm()

    def test_invoice_created_for_ordered_qty(self):
        """Invoice is created with the full ordered quantity."""
        invoice = self.order._create_offline_invoice_from_ordered_qty()
        self.assertTrue(invoice, "An invoice should be created.")
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertAlmostEqual(invoice.amount_untaxed, 150.0)

    def test_no_invoice_created_when_already_invoiced(self):
        """No invoice is created if all lines are already fully invoiced."""
        # Create and post first invoice
        inv = self.order._create_offline_invoice_from_ordered_qty()
        inv.action_post()
        # Now qty_invoiced == product_uom_qty → nothing to invoice
        invoice2 = self.order._create_offline_invoice_from_ordered_qty()
        self.assertFalse(invoice2.id if invoice2 else False,
                         "No invoice should be created when already fully invoiced.")


@tagged('post_install', '-at_install', 'offline_sale')
class TestProcessOfflineInvoicePayment(TransactionCase):
    """Tests for SaleOrder._process_offline_invoice_payment."""

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Payment Test Product',
            'type': 'consu',
            'invoice_policy': 'order',
            'lst_price': 200.0,
        })
        self.partner = self.env['res.partner'].create({'name': 'Payment Partner'})
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 200.0,
            })],
        })
        self.order.action_confirm()

    def test_full_payment_marks_invoice_paid(self):
        """Paying the full amount results in invoice payment_state 'paid' or 'in_payment'."""
        # Use amount_total (not a hardcoded value) so the test passes even
        # when the environment has sales taxes that increase the invoice total.
        self.env['sale.order']._process_offline_invoice_payment(
            self.order, {'amount_paid': self.order.amount_total}
        )
        invoice = self.order.invoice_ids.filtered(lambda m: m.state != 'cancel')[:1]
        self.assertTrue(invoice)
        self.assertIn(invoice.payment_state, ('paid', 'in_payment'))

    def test_partial_payment_leaves_residual(self):
        """Partial payment leaves amount_residual > 0."""
        self.env['sale.order']._process_offline_invoice_payment(
            self.order, {'amount_paid': 100.0}
        )
        invoice = self.order.invoice_ids.filtered(lambda m: m.state != 'cancel')[:1]
        self.assertTrue(invoice)
        self.assertGreater(invoice.amount_residual, 0)

    def test_zero_payment_does_not_register_payment(self):
        """A zero amount_paid only posts the invoice without creating a payment."""
        self.env['sale.order']._process_offline_invoice_payment(
            self.order, {'amount_paid': 0.0}
        )
        invoice = self.order.invoice_ids.filtered(lambda m: m.state != 'cancel')[:1]
        self.assertTrue(invoice, "Invoice should exist even with zero payment.")
        self.assertEqual(invoice.payment_state, 'not_paid',
                         "Invoice should remain unpaid when amount_paid is 0.")


@tagged('post_install', '-at_install', 'offline_sale')
class TestGetPendingSaleOrders(TransactionCase):
    """Tests for SaleOrder.get_pending_sale_orders."""

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Pending Order Product',
            'type': 'consu',
            'invoice_policy': 'order',
            'lst_price': 100.0,
        })
        self.partner = self.env['res.partner'].create({'name': 'Pending Customer'})

    def _create_order(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })
        return order

    def test_draft_order_is_included(self):
        """Draft orders without invoices appear in pending orders."""
        order = self._create_order()
        pending = self.env['sale.order'].get_pending_sale_orders()
        ids = [p['id'] for p in pending]
        self.assertIn(order.id, ids)

    def test_fully_paid_order_is_excluded(self):
        """Fully paid orders are excluded from pending list."""
        order = self._create_order()
        order.action_confirm()
        # Pay order.amount_total (not a hardcoded value) so the invoice is
        # fully settled even when taxes are applied in the test environment.
        self.env['sale.order']._process_offline_invoice_payment(
            order, {'amount_paid': order.amount_total}
        )
        pending = self.env['sale.order'].get_pending_sale_orders()
        ids = [p['id'] for p in pending]
        self.assertNotIn(order.id, ids)

    def test_result_contains_required_keys(self):
        """Each pending order dict contains the expected keys."""
        self._create_order()
        pending = self.env['sale.order'].get_pending_sale_orders()
        self.assertTrue(pending, "There should be at least one pending order.")
        required_keys = {'id', 'name', 'date', 'state', 'partner_id', 'partner_name',
                         'amount_total', 'amount_residual', 'lines'}
        self.assertTrue(required_keys.issubset(set(pending[0].keys())))

    def test_cancelled_order_excluded(self):
        """Cancelled orders are excluded from pending list."""
        order = self._create_order()
        order.action_cancel()
        pending = self.env['sale.order'].get_pending_sale_orders()
        ids = [p['id'] for p in pending]
        self.assertNotIn(order.id, ids)


@tagged('post_install', '-at_install', 'offline_sale')
class TestGetOfflineData(TransactionCase):
    """Tests for SaleOrder.get_offline_data."""

    def test_returns_expected_top_level_keys(self):
        """get_offline_data returns a dict with all required top-level keys."""
        data = self.env['sale.order'].get_offline_data()
        required = {'products', 'partners', 'categories', 'company',
                    'user_name', 'payment_terms', 'taxes'}
        self.assertTrue(required.issubset(set(data.keys())))

    def test_products_are_saleable(self):
        """Only products marked as sale_ok are returned."""
        # Create a non-saleable product that should not appear
        self.env['product.product'].create({
            'name': 'Non Saleable',
            'sale_ok': False,
        })
        data = self.env['sale.order'].get_offline_data()
        # All returned products must be saleable (we can check via the DB)
        product_ids = [p['id'] for p in data['products']]
        non_sale = self.env['product.product'].browse(product_ids).filtered(
            lambda p: not p.sale_ok
        )
        self.assertFalse(non_sale, "Non-saleable products should not be included.")

    def test_company_info_has_name(self):
        """Company info dict includes a 'name' key with a value."""
        data = self.env['sale.order'].get_offline_data()
        self.assertIn('name', data['company'])
        self.assertTrue(data['company']['name'])

    def test_taxes_only_sale_type(self):
        """Returned taxes are all of type_tax_use='sale'."""
        data = self.env['sale.order'].get_offline_data()
        if data['taxes']:
            tax_ids = [t['id'] for t in data['taxes']]
            taxes = self.env['account.tax'].browse(tax_ids)
            non_sale_taxes = taxes.filtered(lambda t: t.type_tax_use != 'sale')
            self.assertFalse(non_sale_taxes)
