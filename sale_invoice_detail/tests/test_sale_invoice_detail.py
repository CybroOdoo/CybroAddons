# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestSaleInvoiceDetail(common.TransactionCase):
    """Test suite for sale_invoice_detail module covering invoiced amount,
    paid amount, due amount, percentage calculation, payment count,
    view architecture, salesperson access rights, and refund handling."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create customer partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Invoice Detail Partner',
            'email': 'partner@invoicedetail.com',
        })

        # Create product without taxes for exact amount math
        cls.product = cls.env['product.product'].create({
            'name': 'Detail Test Product',
            'list_price': 100.0,
            'taxes_id': [(5, 0, 0)],
        })

        # Sales Order 1: 2 units = 200.0
        cls.order_1 = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
            })],
        })

        # Sales Order 2: 1 unit = 100.0
        cls.order_2 = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
            })],
        })

        # Zero-amount Sales Order
        cls.zero_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 0.0,
                'tax_ids': [(5, 0, 0)],
            })],
        })

    def _create_and_post_payment(self, amount, memo, state='paid'):
        """Helper to create payment with given memo and state."""
        pay = self.env['account.payment'].create({
            'partner_id': self.partner.id,
            'amount': amount,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'memo': memo,
        })
        if state == 'paid':
            pay.action_post()
        return pay

    def test_01_views_structure(self):
        """Verify the tree and form views exist and can be loaded without XML errors."""
        tree_view = self.env.ref('sale_invoice_detail.view_order_tree')
        form_view = self.env.ref('sale_invoice_detail.view_order_form')
        self.assertTrue(tree_view, "view_order_tree must exist.")
        self.assertTrue(form_view, "view_order_form must exist.")

        views = self.env['sale.order'].get_views([(tree_view.id, 'list'), (form_view.id, 'form')])
        self.assertIn('list', views.get('views', {}))
        self.assertIn('form', views.get('views', {}))

    def test_02_sale_order_before_invoice(self):
        """Verify fields on a sale order before any invoice is created."""
        self.order_1.action_confirm()
        self.order_1.invalidate_recordset()

        self.assertEqual(self.order_1.invoiced_amount, 0.0)
        self.assertEqual(self.order_1.paid_amount, 0.0)
        self.assertEqual(self.order_1.due_amount, 0.0)
        self.assertEqual(self.order_1.paid_amount_percent, 0.0)
        self.assertEqual(self.order_1.payment_count, 0)

        # Without invoice_ids, action_view_payments returns None
        action = self.order_1.action_view_payments()
        self.assertIsNone(action, "action_view_payments should return None when order has no invoices.")

    def test_03_sale_order_invoiced_no_payment(self):
        """Verify amounts when an order is invoiced but no payments have been registered."""
        self.order_1.action_confirm()
        invoices = self.order_1._create_invoices()
        invoices.action_post()
        self.order_1.invalidate_recordset()

        self.assertEqual(self.order_1.invoiced_amount, 200.0)
        self.assertEqual(self.order_1.paid_amount, 0.0)
        self.assertEqual(self.order_1.due_amount, 200.0)
        self.assertEqual(self.order_1.paid_amount_percent, 0.0)
        self.assertEqual(self.order_1.payment_count, 0)

        # action_view_payments returns action with empty domain when invoices exist but no payments
        action = self.order_1.action_view_payments()
        self.assertIsNotNone(action)
        self.assertEqual(action.get('res_model'), 'account.payment')
        self.assertEqual(action.get('domain'), [('id', 'in', [])])

    def test_04_partial_payment(self):
        """Verify amounts and percentages when a partial payment is registered."""
        self.order_1.action_confirm()
        invoices = self.order_1._create_invoices()
        invoices.action_post()

        payment = self._create_and_post_payment(50.0, invoices.name, state='paid')
        self.order_1.invalidate_recordset()

        self.assertEqual(self.order_1.invoiced_amount, 200.0)
        self.assertEqual(self.order_1.paid_amount, 50.0)
        self.assertEqual(self.order_1.due_amount, 150.0)
        self.assertAlmostEqual(self.order_1.paid_amount_percent, 25.0)
        self.assertEqual(self.order_1.payment_count, 1)

        action = self.order_1.action_view_payments()
        self.assertEqual(action.get('res_model'), 'account.payment')
        self.assertEqual(action.get('domain'), [('id', 'in', [payment.id])])
        self.assertEqual(action.get('context'), {'create': False})

    def test_05_multiple_payments_and_full_payment(self):
        """Verify amounts and percentages when multiple payments complete the invoice."""
        self.order_1.action_confirm()
        invoices = self.order_1._create_invoices()
        invoices.action_post()

        pay_1 = self._create_and_post_payment(50.0, invoices.name, state='paid')
        pay_2 = self._create_and_post_payment(150.0, invoices.name, state='paid')
        self.order_1.invalidate_recordset()

        self.assertEqual(self.order_1.invoiced_amount, 200.0)
        self.assertEqual(self.order_1.paid_amount, 200.0)
        self.assertEqual(self.order_1.due_amount, 0.0)
        self.assertAlmostEqual(self.order_1.paid_amount_percent, 100.0)
        self.assertEqual(self.order_1.payment_count, 2)

        action = self.order_1.action_view_payments()
        self.assertEqual(action.get('res_model'), 'account.payment')
        allowed_ids = action.get('domain', [])[0][2]
        self.assertIn(pay_1.id, allowed_ids)
        self.assertIn(pay_2.id, allowed_ids)

    def test_06_draft_and_cancelled_invoices_excluded(self):
        """Verify that draft and cancelled invoices do not contribute to invoiced_amount."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
            })],
        })
        order.action_confirm()

        # Draft invoice
        draft_inv = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
                'sale_line_ids': [(6, 0, [order.order_line[0].id])],
            })],
        })
        self.assertEqual(draft_inv.state, 'draft')
        order.invalidate_recordset()
        self.assertEqual(order.invoiced_amount, 0.0, "Draft invoice must not be counted in invoiced_amount.")
        self.assertEqual(order.payment_count, 0)

        # Post the invoice
        draft_inv.action_post()
        order.invalidate_recordset()
        self.assertEqual(order.invoiced_amount, 100.0)

        # Create draft payment without posting
        draft_pay = self._create_and_post_payment(50.0, draft_inv.name, state='draft')
        self.assertEqual(draft_pay.state, 'draft')
        order.invalidate_recordset()
        self.assertEqual(order.paid_amount, 0.0, "Draft payment must not be counted in paid_amount.")
        self.assertEqual(order.payment_count, 0)

        # Cancel the invoice
        draft_inv.button_cancel()
        self.assertEqual(draft_inv.state, 'cancel')
        order.invalidate_recordset()
        self.assertEqual(order.invoiced_amount, 0.0, "Cancelled invoice must not be counted in invoiced_amount.")
        self.assertEqual(order.due_amount, 0.0)

    def test_07_multiple_invoices_on_single_order(self):
        """Verify computation when an order has multiple posted invoices."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                    'tax_ids': [(5, 0, 0)],
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                    'tax_ids': [(5, 0, 0)],
                }),
            ],
        })
        order.action_confirm()

        # Create first invoice for line 1
        inv_1 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
                'sale_line_ids': [(6, 0, [order.order_line[0].id])],
            })],
        })
        inv_1.action_post()

        # Create second invoice for line 2
        inv_2 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
                'sale_line_ids': [(6, 0, [order.order_line[1].id])],
            })],
        })
        inv_2.action_post()

        order.invalidate_recordset()
        self.assertEqual(order.invoiced_amount, 200.0)

        # Pay invoice 1 in full (100.0) and invoice 2 partially (50.0)
        pay_1 = self._create_and_post_payment(100.0, inv_1.name, state='paid')
        pay_2 = self._create_and_post_payment(50.0, inv_2.name, state='paid')

        order.invalidate_recordset()
        self.assertEqual(order.paid_amount, 150.0)
        self.assertEqual(order.due_amount, 50.0)
        self.assertAlmostEqual(order.paid_amount_percent, 75.0)
        self.assertEqual(order.payment_count, 2)

        action = order.action_view_payments()
        allowed_ids = action.get('domain', [])[0][2]
        self.assertIn(pay_1.id, allowed_ids)
        self.assertIn(pay_2.id, allowed_ids)

    def test_08_refund_credit_note_handling(self):
        """Verify credit notes (out_refund) properly reduce invoiced_amount and due_amount."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
            })],
        })
        order.action_confirm()

        # Create out_invoice for 200.0
        inv = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 2.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
                'sale_line_ids': [(6, 0, [order.order_line[0].id])],
            })],
        })
        inv.action_post()
        order.invalidate_recordset()
        self.assertEqual(order.invoiced_amount, 200.0)

        # Create out_refund (credit note) for 50.0
        refund = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 50.0,
                'tax_ids': [(5, 0, 0)],
                'sale_line_ids': [(6, 0, [order.order_line[0].id])],
            })],
        })
        refund.action_post()

        order.invalidate_recordset()
        # Invoiced amount should now be 200.0 - 50.0 = 150.0
        self.assertEqual(order.invoiced_amount, 150.0)
        self.assertEqual(order.due_amount, 150.0)

        # Pay remaining 150.0
        self._create_and_post_payment(150.0, inv.name, state='paid')
        order.invalidate_recordset()
        self.assertEqual(order.paid_amount, 150.0)
        self.assertEqual(order.due_amount, 0.0)
        self.assertAlmostEqual(order.paid_amount_percent, 75.0)

    def test_09_multi_recordset_computation(self):
        """Verify compute methods work seamlessly on recordsets with multiple sale orders."""
        self.order_1.action_confirm()
        self.order_2.action_confirm()

        inv_1 = self.order_1._create_invoices()
        inv_1.action_post()
        self._create_and_post_payment(200.0, inv_1.name, state='paid')

        inv_2 = self.order_2._create_invoices()
        inv_2.action_post()
        self._create_and_post_payment(40.0, inv_2.name, state='paid')

        orders = self.order_1 + self.order_2
        orders.invalidate_recordset()

        self.assertEqual(self.order_1.invoiced_amount, 200.0)
        self.assertEqual(self.order_1.paid_amount, 200.0)
        self.assertEqual(self.order_1.due_amount, 0.0)
        self.assertAlmostEqual(self.order_1.paid_amount_percent, 100.0)
        self.assertEqual(self.order_1.payment_count, 1)

        self.assertEqual(self.order_2.invoiced_amount, 100.0)
        self.assertEqual(self.order_2.paid_amount, 40.0)
        self.assertEqual(self.order_2.due_amount, 60.0)
        self.assertAlmostEqual(self.order_2.paid_amount_percent, 40.0)
        self.assertEqual(self.order_2.payment_count, 1)

    def test_10_zero_amount_order_handling(self):
        """Verify _compute_paid_amount_percent handles amount_total == 0 gracefully."""
        self.zero_order.action_confirm()
        self.assertEqual(self.zero_order.amount_total, 0.0)
        self.zero_order.invalidate_recordset()

        self.assertEqual(self.zero_order.paid_amount_percent, 0.0)

    def test_11_stat_button_invisibility_and_view_validation(self):
        """Exercise the form view architecture to ensure the stat button evaluates properly,
        and views render without errors."""
        form_view = self.env.ref('sale_invoice_detail.view_order_form')
        views_dict = self.env['sale.order'].get_views([(form_view.id, 'form')])
        form_arch = views_dict.get('views', {}).get('form', {}).get('arch', '')

        # Verify action_view_payments button and paid_amount_percent are present with invisibility condition
        self.assertIn('invisible="payment_count == 0"', form_arch, "action_view_payments must have invisible condition.")
        self.assertIn('name="action_view_payments"', form_arch, "action_view_payments button must exist in arch.")
        self.assertIn('name="paid_amount_percent"', form_arch, "paid_amount_percent field must exist in arch.")

        # Test state before payment: payment_count is 0
        self.order_1.action_confirm()
        self.order_1.invalidate_recordset()
        self.assertEqual(self.order_1.payment_count, 0)

        # After invoice and payment: payment_count becomes 1
        invoices = self.order_1._create_invoices()
        invoices.action_post()
        self._create_and_post_payment(100.0, invoices.name, state='paid')
        self.order_1.invalidate_recordset()
        self.assertEqual(self.order_1.payment_count, 1)

    def test_12_sales_user_access_rights(self):
        """Verify that a standard sales user without accounting permissions can create
        sale orders, view computed amounts, retrieve payments, and view payments."""
        salesman_group = self.env.ref('sales_team.group_sale_salesman')
        user_group = self.env.ref('base.group_user')
        sales_user = self.env['res.users'].create({
            'name': 'Test Salesperson User',
            'login': 'test_salesperson_user',
            'email': 'salesuser@example.com',
            'group_ids': [(6, 0, [user_group.id, salesman_group.id])],
        })

        # Ensure salesperson has no accounting privileges
        account_group = self.env.ref('account.group_account_invoice', raise_if_not_found=False)
        if account_group:
            self.assertNotIn(account_group.id, sales_user.group_ids.ids)
        account_ro = self.env.ref('account.group_account_readonly', raise_if_not_found=False)
        if account_ro:
            self.assertNotIn(account_ro.id, sales_user.group_ids.ids)

        # Create order as the salesperson
        order = self.env['sale.order'].with_user(sales_user).create({
            'partner_id': self.partner.id,
            'user_id': sales_user.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
            })],
        })
        order.action_confirm()

        inv = order._create_invoices()
        inv.action_post()
        payment = self._create_and_post_payment(100.0, inv.name, state='paid')

        # Read fields as the salesperson user
        order_as_salesman = order.with_user(sales_user)
        values = order_as_salesman.read([
            'invoiced_amount',
            'paid_amount',
            'due_amount',
            'paid_amount_percent',
            'payment_count',
        ])
        self.assertTrue(values, "Salesperson should be able to read sale order fields.")
        self.assertEqual(values[0]['invoiced_amount'], 200.0)
        self.assertEqual(values[0]['paid_amount'], 100.0)
        self.assertEqual(values[0]['due_amount'], 100.0)
        self.assertEqual(values[0]['payment_count'], 1)

        # Exercise get_views as the salesperson user
        form_view = self.env.ref('sale_invoice_detail.view_order_form')
        tree_view = self.env.ref('sale_invoice_detail.view_order_tree')
        views = self.env['sale.order'].with_user(sales_user).get_views(
            [(form_view.id, 'form'), (tree_view.id, 'list')]
        )
        self.assertIn('form', views.get('views', {}))
        self.assertIn('list', views.get('views', {}))

        # Exercise action_view_payments and verify salesperson can access payments
        action = order_as_salesman.action_view_payments()
        self.assertIsNotNone(action)
        self.assertEqual(action.get('res_model'), 'account.payment')
        self.assertEqual(action.get('domain'), [('id', 'in', [payment.id])])

        # Test reading the payments as salesperson user
        payments = self.env['account.payment'].with_user(sales_user).search([
            ('id', 'in', payment.ids),
        ])
        self.assertTrue(payments, "Salesperson should be able to read order payments.")
        self.assertEqual(payments.amount, 100.0)

    def test_13_sales_user_third_party_invoice_access(self):
        """Verify that when invoices on a sales order are created by an accounting user
        or another user, the salesperson can still view their order amounts accurately."""
        salesman_group = self.env.ref('sales_team.group_sale_salesman')
        user_group = self.env.ref('base.group_user')
        sales_user = self.env['res.users'].create({
            'name': 'Sales User Third Party',
            'login': 'test_sales_user_tp',
            'email': 'salesusertp@example.com',
            'group_ids': [(6, 0, [user_group.id, salesman_group.id])],
        })

        order = self.env['sale.order'].with_user(sales_user).create({
            'partner_id': self.partner.id,
            'user_id': sales_user.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
            })],
        })
        order.action_confirm()

        # Invoice created by admin with invoice_user_id != sales_user
        inv = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_user_id': self.env.ref('base.user_admin').id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 2.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
                'sale_line_ids': [(6, 0, [order.order_line[0].id])],
            })],
        })
        inv.action_post()
        self._create_and_post_payment(100.0, inv.name, state='paid')

        # Read order as salesperson
        order_as_salesman = order.with_user(sales_user)
        order_as_salesman.invalidate_recordset()
        self.assertEqual(order_as_salesman.invoiced_amount, 200.0)
        self.assertEqual(order_as_salesman.paid_amount, 100.0)
        self.assertEqual(order_as_salesman.due_amount, 100.0)
        self.assertEqual(order_as_salesman.payment_count, 1)

        # Salesperson can retrieve order payments without AccessError
        payments = order_as_salesman._get_order_payments()
        self.assertEqual(len(payments), 1)
        action = order_as_salesman.action_view_payments()
        self.assertIsNotNone(action)
        self.assertEqual(action.get('res_model'), 'account.payment')

    def test_14_unauthorized_user_access_error(self):
        """Verify that a sales user cannot access payments or details of another user's order."""
        salesman_group = self.env.ref('sales_team.group_sale_salesman')
        user_group = self.env.ref('base.group_user')
        sales_user_1 = self.env['res.users'].create({
            'name': 'Sales User 1',
            'login': 'test_sales_user_1',
            'email': 'salesuser1@example.com',
            'group_ids': [(6, 0, [user_group.id, salesman_group.id])],
        })
        sales_user_2 = self.env['res.users'].create({
            'name': 'Sales User 2',
            'login': 'test_sales_user_2',
            'email': 'salesuser2@example.com',
            'group_ids': [(6, 0, [user_group.id, salesman_group.id])],
        })

        order_user_1 = self.env['sale.order'].with_user(sales_user_1).create({
            'partner_id': self.partner.id,
            'user_id': sales_user_1.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
            })],
        })
        order_user_1.action_confirm()

        # Sales user 2 cannot access payments of sales user 1's order
        order_as_user_2 = order_user_1.with_user(sales_user_2)
        with self.assertRaises(AccessError):
            order_as_user_2._get_order_payments()
        with self.assertRaises(AccessError):
            order_as_user_2.action_view_payments()

    def test_15_multi_company_payment_isolation(self):
        """Verify that _get_order_payments does not leak payments from other companies."""
        company_2 = self.env['res.company'].create({'name': 'Test Company 2'})
        transfer_acc = self.env.company.transfer_account_id
        if transfer_acc:
            transfer_acc.company_ids = [(4, company_2.id)]
            company_2.transfer_account_id = transfer_acc
        journal_2 = self.env['account.journal'].create({
            'name': 'Bank Company 2',
            'code': 'BNK2',
            'type': 'bank',
            'company_id': company_2.id,
        })

        self.order_1.action_confirm()
        inv_1 = self.order_1._create_invoices()
        inv_1.action_post()
        pay_1 = self._create_and_post_payment(100.0, inv_1.name, state='paid')

        # Create payment in company 2 with the same memo
        pay_2 = self.env['account.payment'].create({
            'partner_id': self.partner.id,
            'amount': 100.0,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'memo': inv_1.name,
            'company_id': company_2.id,
            'journal_id': journal_2.id,
        })

        payments = self.order_1._get_order_payments()
        self.assertIn(pay_1.id, payments.ids)
        self.assertNotIn(pay_2.id, payments.ids, "Payments from other companies must not be linked.")

    def test_16_get_order_payments_without_posted_invoices(self):
        """Verify _get_order_payments directly when an order has no posted invoices."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
            })],
        })
        payments = order._get_order_payments()
        self.assertFalse(payments, "_get_order_payments should return empty recordset when no posted invoices exist.")
        self.assertEqual(payments._name, 'account.payment')

    def test_17_invoiced_amount_zero_or_negative_refund(self):
        """Verify amounts when posted refund matches or exceeds invoiced amount resulting in invoiced_amount <= 0."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
            })],
        })
        order.action_confirm()

        inv = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
                'sale_line_ids': [(6, 0, [order.order_line[0].id])],
            })],
        })
        inv.action_post()

        # Create refund that matches invoice amount
        refund = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 100.0,
                'tax_ids': [(5, 0, 0)],
                'sale_line_ids': [(6, 0, [order.order_line[0].id])],
            })],
        })
        refund.action_post()

        order.invalidate_recordset()
        self.assertEqual(order.invoiced_amount, 0.0)
        self.assertEqual(order.paid_amount, 0.0)
        self.assertEqual(order.due_amount, 0.0)
        self.assertEqual(order.paid_amount_percent, 0.0)

    def test_18_fetch_exception_fallback_to_sudo(self):
        """Verify fallback to sudo invoices if fetch raises an exception."""
        self.order_1.action_confirm()
        inv = self.order_1._create_invoices()
        inv.action_post()
        self._create_and_post_payment(50.0, inv.name, state='paid')

        with patch.object(type(self.order_1.invoice_ids), 'fetch', side_effect=AccessError('Simulated error')):
            payments = self.order_1._get_order_payments()
            self.assertEqual(len(payments), 1)
            action = self.order_1.action_view_payments()
            self.assertIsNotNone(action)


