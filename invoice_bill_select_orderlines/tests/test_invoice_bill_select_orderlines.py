###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

PURCHASE_MODULE = ('odoo.addons.invoice_bill_select_orderlines.models.'
                   'purchase_order')


@tagged('post_install', '-at_install')
class TestInvoiceBillSelectOrderLines(AccountTestInvoicingCommon):
    """Tests for invoicing / billing only the selected order lines.

    ``AccountTestInvoicingCommon`` loads a chart of accounts, which creates
    the sale and purchase journals needed to generate invoices and bills. A
    plain ``TransactionCase`` runs on a database without a chart of accounts
    and fails with "No journal could be found"."""

    @classmethod
    def get_default_groups(cls):
        """Also give the test user the Sales Administrator rights, so it can
        create and invoice sale orders besides purchase orders and bills."""
        return super().get_default_groups() | cls.quick_ref(
            'sales_team.group_sale_manager')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create(
            {'name': 'Test Partner'})
        cls.product_1 = cls.env['product.product'].create(
            {'name': 'Test Product 1', 'type': 'service'})
        cls.product_2 = cls.env['product.product'].create(
            {'name': 'Test Product 2', 'type': 'service'})
        cls.product_3 = cls.env['product.product'].create(
            {'name': 'Test Product 3', 'type': 'service'})

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _product_lines(self, move):
        return move.invoice_line_ids.filtered(
            lambda line: line.display_type == 'product')

    def _section_lines(self, move):
        return move.invoice_line_ids.filtered(
            lambda line: line.display_type == 'line_section')

    def _create_confirmed_sale_order(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {'product_id': self.product_1.id,
                        'product_uom_qty': 2}),
                (0, 0, {'product_id': self.product_2.id,
                        'product_uom_qty': 3}),
                (0, 0, {'product_id': self.product_3.id,
                        'product_uom_qty': 1}),
            ],
        })
        sale_order.action_confirm()
        return sale_order

    def _create_confirmed_purchase_order(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {'product_id': self.product_1.id,
                        'product_qty': 2, 'price_unit': 100}),
                (0, 0, {'product_id': self.product_2.id,
                        'product_qty': 3, 'price_unit': 200}),
                (0, 0, {'product_id': self.product_3.id,
                        'product_qty': 1, 'price_unit': 50}),
            ],
        })
        purchase_order.button_confirm()
        return purchase_order

    def _create_sectioned_purchase_order(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {'display_type': 'line_section',
                        'name': 'Section A', 'product_qty': 0}),
                (0, 0, {'product_id': self.product_1.id,
                        'product_qty': 1, 'price_unit': 10}),
                (0, 0, {'display_type': 'line_section',
                        'name': 'Section B', 'product_qty': 0}),
                (0, 0, {'product_id': self.product_2.id,
                        'product_qty': 1, 'price_unit': 20}),
                (0, 0, {'display_type': 'line_section',
                        'name': 'Section C', 'product_qty': 0}),
                (0, 0, {'product_id': self.product_3.id,
                        'product_qty': 1, 'price_unit': 30}),
            ],
        })
        purchase_order.button_confirm()
        return purchase_order

    def _purchase_line(self, order, product):
        return order.order_line.filtered(
            lambda line: line.product_id == product)

    def _force_not_to_invoice(self, order):
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE purchase_order SET invoice_status = 'no' WHERE id = %s",
            [order.id])
        order.invalidate_recordset(['invoice_status'])

    # -------------------------------------------------------------------------
    # Sale Order Tests
    # -------------------------------------------------------------------------

    def test_sale_single_line_selected_for_invoice(self):
        sale_order = self._create_confirmed_sale_order()
        sale_order.order_line[0].is_product_select = True
        sale_order.order_line[1].is_product_select = False
        sale_order.order_line[2].is_product_select = False
        invoice = sale_order._create_invoices()
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(
            invoice.invoice_line_ids[0].product_id, self.product_1)

    def test_sale_multiple_lines_selected_for_invoice(self):
        sale_order = self._create_confirmed_sale_order()
        sale_order.order_line[0].is_product_select = True
        sale_order.order_line[1].is_product_select = True
        sale_order.order_line[2].is_product_select = False
        invoice = sale_order._create_invoices()
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        invoiced_products = invoice.invoice_line_ids.mapped('product_id')
        self.assertIn(self.product_1, invoiced_products)
        self.assertIn(self.product_2, invoiced_products)
        self.assertNotIn(self.product_3, invoiced_products)

    def test_sale_no_line_selected_raises_user_error(self):
        sale_order = self._create_confirmed_sale_order()
        for line in sale_order.order_line:
            line.is_product_select = False
        with self.assertRaises(UserError):
            sale_order._create_invoices()

    def test_sale_action_select_all(self):
        sale_order = self._create_confirmed_sale_order()
        for line in sale_order.order_line:
            line.is_product_select = False
        sale_order.action_select_all()
        self.assertTrue(
            all(sale_order.order_line.mapped('is_product_select')))

    def test_sale_action_deselect_all(self):
        sale_order = self._create_confirmed_sale_order()
        for line in sale_order.order_line:
            line.is_product_select = True
        sale_order.action_deselect_all()
        self.assertFalse(
            any(sale_order.order_line.mapped('is_product_select')))

    def test_sale_is_qty_to_invoice_computed_field(self):
        sale_order = self._create_confirmed_sale_order()
        self.assertFalse(
            sale_order.is_qty_to_invoice,
            "is_qty_to_invoice should be False when a line is not selected")
        sale_order.order_line[0].is_product_select = True
        sale_order.order_line[1].is_product_select = True
        sale_order.order_line[2].is_product_select = True
        sale_order._compute_is_qty_to_invoice()
        self.assertTrue(
            sale_order.is_qty_to_invoice,
            "is_qty_to_invoice should be True when all lines are selected")

    def test_sale_invoice_qty_matches_order_line_qty(self):
        sale_order = self._create_confirmed_sale_order()
        sale_order.order_line[0].is_product_select = True
        sale_order.order_line[1].is_product_select = False
        sale_order.order_line[2].is_product_select = False
        invoice = sale_order._create_invoices()
        self.assertEqual(invoice.invoice_line_ids[0].quantity, 2)

    def test_sale_is_product_select_not_copied(self):
        sale_order = self._create_confirmed_sale_order()
        sale_order.order_line[0].is_product_select = True
        copied_order = sale_order.copy()
        self.assertFalse(
            any(copied_order.order_line.mapped('is_product_select')),
            "is_product_select must not be copied to the duplicated order")

    def test_sale_draft_order_is_qty_to_invoice_true(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {'product_id': self.product_1.id,
                                   'product_uom_qty': 1})],
        })
        self.assertEqual(sale_order.invoice_status, 'no')
        self.assertTrue(sale_order.is_qty_to_invoice)

    def test_sale_nothing_to_invoice_returns_empty_lines(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {'product_id': self.product_1.id,
                                   'product_uom_qty': 1})],
        })
        self.assertFalse(sale_order._get_invoiceable_lines())

    def test_sale_only_section_of_selected_line_is_invoiced(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {'display_type': 'line_section',
                        'name': 'Section A'}),
                (0, 0, {'product_id': self.product_1.id,
                        'product_uom_qty': 1}),
                (0, 0, {'display_type': 'line_section',
                        'name': 'Section B'}),
                (0, 0, {'product_id': self.product_2.id,
                        'product_uom_qty': 1}),
            ],
        })
        sale_order.action_confirm()
        sale_order.order_line.filtered(
            lambda line: line.product_id == self.product_2,
        ).is_product_select = True
        invoice = sale_order._create_invoices()
        self.assertEqual(self._section_lines(invoice).mapped('name'),
                         ['Section B'])
        self.assertEqual(self._product_lines(invoice).product_id,
                         self.product_2)

    def test_sale_subsection_of_selected_line_is_invoiced(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {'display_type': 'line_section',
                        'name': 'Section A'}),
                (0, 0, {'display_type': 'line_subsection',
                        'name': 'Sub A1'}),
                (0, 0, {'product_id': self.product_1.id,
                        'product_uom_qty': 1}),
                (0, 0, {'display_type': 'line_subsection',
                        'name': 'Sub A2'}),
                (0, 0, {'product_id': self.product_2.id,
                        'product_uom_qty': 1}),
            ],
        })
        sale_order.action_confirm()
        sale_order.order_line.filtered(
            lambda line: line.product_id == self.product_2,
        ).is_product_select = True
        invoice = sale_order._create_invoices()
        headings = invoice.invoice_line_ids.filtered(
            lambda line: line.display_type in (
                'line_section', 'line_subsection'))
        self.assertEqual(headings.mapped('name'), ['Section A', 'Sub A2'])
        self.assertEqual(self._product_lines(invoice).product_id,
                         self.product_2)

    def test_sale_fully_invoiced_order_hides_select_buttons(self):
        sale_order = self._create_confirmed_sale_order()
        sale_order.action_select_all()
        sale_order._create_invoices()
        self.assertTrue(
            sale_order.is_qty_to_invoice,
            "Select/Deselect buttons must be hidden on a fully invoiced "
            "order")

    def test_sale_selection_cleared_after_invoice(self):
        sale_order = self._create_confirmed_sale_order()
        sale_order.action_select_all()
        sale_order._create_invoices()
        self.assertFalse(
            any(sale_order.order_line.mapped('is_product_select')))

    # -------------------------------------------------------------------------
    # Purchase Order Tests
    # -------------------------------------------------------------------------

    def test_purchase_single_line_selected_for_bill(self):
        purchase_order = self._create_confirmed_purchase_order()
        purchase_order.order_line[0].is_product_select = False
        purchase_order.order_line[1].is_product_select = True
        purchase_order.order_line[2].is_product_select = False
        action = purchase_order.action_create_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(
            invoice.invoice_line_ids[0].product_id, self.product_2)

    def test_purchase_multiple_lines_selected_for_bill(self):
        purchase_order = self._create_confirmed_purchase_order()
        purchase_order.order_line[0].is_product_select = True
        purchase_order.order_line[1].is_product_select = True
        purchase_order.order_line[2].is_product_select = False
        action = purchase_order.action_create_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        invoiced_products = invoice.invoice_line_ids.mapped('product_id')
        self.assertIn(self.product_1, invoiced_products)
        self.assertIn(self.product_2, invoiced_products)
        self.assertNotIn(self.product_3, invoiced_products)

    def test_purchase_no_line_selected_raises_user_error(self):
        purchase_order = self._create_confirmed_purchase_order()
        for line in purchase_order.order_line:
            line.is_product_select = False
        with self.assertRaises(UserError):
            purchase_order.action_create_invoice()

    def test_purchase_action_select_all(self):
        purchase_order = self._create_confirmed_purchase_order()
        for line in purchase_order.order_line:
            line.is_product_select = False
        purchase_order.action_select_all()
        self.assertTrue(
            all(purchase_order.order_line.mapped('is_product_select')))

    def test_purchase_action_deselect_all(self):
        purchase_order = self._create_confirmed_purchase_order()
        for line in purchase_order.order_line:
            line.is_product_select = True
        purchase_order.action_deselect_all()
        self.assertFalse(
            any(purchase_order.order_line.mapped('is_product_select')))

    def test_purchase_all_lines_selected_computed_field(self):
        purchase_order = self._create_confirmed_purchase_order()
        for line in purchase_order.order_line:
            line.is_product_select = True
        purchase_order._compute_selection_states()
        self.assertTrue(purchase_order.all_lines_selected)
        self.assertTrue(purchase_order.any_line_selected)

    def test_purchase_any_line_selected_computed_field(self):
        purchase_order = self._create_confirmed_purchase_order()
        purchase_order.order_line[0].is_product_select = True
        purchase_order.order_line[1].is_product_select = False
        purchase_order.order_line[2].is_product_select = False
        purchase_order._compute_selection_states()
        self.assertFalse(purchase_order.all_lines_selected)
        self.assertTrue(purchase_order.any_line_selected)

    def test_purchase_no_selection_computed_field(self):
        purchase_order = self._create_confirmed_purchase_order()
        for line in purchase_order.order_line:
            line.is_product_select = False
        purchase_order._compute_selection_states()
        self.assertFalse(purchase_order.all_lines_selected)
        self.assertFalse(purchase_order.any_line_selected)

    def test_purchase_selection_states_without_invoiceable_lines(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {'product_id': self.product_1.id,
                                   'product_qty': 1, 'price_unit': 10})],
        })
        self.assertFalse(purchase_order.all_lines_selected)
        self.assertFalse(purchase_order.any_line_selected)

    def test_purchase_bill_amount_matches_selected_line(self):
        purchase_order = self._create_confirmed_purchase_order()
        purchase_order.order_line[0].is_product_select = True
        purchase_order.order_line[1].is_product_select = False
        purchase_order.order_line[2].is_product_select = False
        action = purchase_order.action_create_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertAlmostEqual(
            invoice.invoice_line_ids[0].price_unit, 100.0)

    def test_purchase_is_product_select_not_copied(self):
        purchase_order = self._create_confirmed_purchase_order()
        purchase_order.order_line[0].is_product_select = True
        copied_order = purchase_order.copy()
        self.assertFalse(
            any(copied_order.order_line.mapped('is_product_select')),
            "is_product_select must not be copied to the duplicated order")

    def test_purchase_only_section_of_selected_line_is_billed(self):
        purchase_order = self._create_sectioned_purchase_order()
        self._purchase_line(
            purchase_order, self.product_2).is_product_select = True
        action = purchase_order.action_create_invoice()
        bill = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(self._section_lines(bill).mapped('name'),
                         ['Section B'])
        self.assertEqual(self._product_lines(bill).product_id,
                         self.product_2)

    def test_purchase_selected_lines_of_two_orders_merge_into_one_bill(self):
        orders = (self._create_confirmed_purchase_order()
                  | self._create_confirmed_purchase_order())
        orders.action_select_all()
        orders.action_create_invoice()
        bills = orders.invoice_ids
        self.assertEqual(len(bills), 1)
        self.assertEqual(len(bills.invoice_line_ids), 6)

    def test_purchase_order_not_to_invoice_is_skipped(self):
        order_1 = self._create_confirmed_purchase_order()
        order_2 = self._create_confirmed_purchase_order()
        orders = order_1 | order_2
        orders.action_select_all()
        self._force_not_to_invoice(order_2)
        action = orders.action_create_invoice()
        bill = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(len(bill.invoice_line_ids), 3)

    def test_purchase_two_vendors_create_two_bills(self):
        other_partner = self.env['res.partner'].create(
            {'name': 'Other Vendor'})
        order_1 = self._create_confirmed_purchase_order()
        order_2 = self.env['purchase.order'].create({
            'partner_id': other_partner.id,
            'order_line': [(0, 0, {'product_id': self.product_1.id,
                                   'product_qty': 1, 'price_unit': 10})],
        })
        order_2.button_confirm()
        orders = order_1 | order_2
        orders.action_select_all()
        orders.action_create_invoice()
        self.assertEqual(len(order_1.invoice_ids), 1)
        self.assertEqual(len(order_2.invoice_ids), 1)
        self.assertNotEqual(order_1.invoice_ids, order_2.invoice_ids)

    def test_purchase_no_order_to_invoice_raises(self):
        purchase_order = self._create_confirmed_purchase_order()
        purchase_order.action_select_all()
        self._force_not_to_invoice(purchase_order)
        with self.assertRaises(UserError):
            purchase_order.action_create_invoice()

    def test_purchase_selected_line_with_negligible_qty_raises(self):
        purchase_order = self._create_confirmed_purchase_order()
        purchase_order.action_select_all()
        with patch(PURCHASE_MODULE + '.float_is_zero', return_value=True), \
                self.assertRaises(UserError):
            purchase_order.action_create_invoice()

    # ---- upload bill flow ---------------------------------------------------

    def test_purchase_action_create_invoice_with_args_uses_upload_flow(self):
        purchase_order = self._create_confirmed_purchase_order()
        with patch.object(type(purchase_order), '_action_upload_bill_selected',
                          return_value='done') as mocked:
            result = purchase_order.action_create_invoice('attachment')
        self.assertEqual(result, 'done')
        mocked.assert_called_once()

    def test_purchase_upload_bill_removes_unselected_lines_and_sections(self):
        purchase_order = self._create_sectioned_purchase_order()
        self._purchase_line(
            purchase_order, self.product_1).is_product_select = True
        purchase_order._action_upload_bill_selected()
        bill = purchase_order.invoice_ids
        self.assertEqual(self._product_lines(bill).product_id,
                         self.product_1)
        self.assertEqual(self._section_lines(bill).mapped('name'),
                         ['Section A'])
        self.assertFalse(
            any(purchase_order.order_line.mapped('is_product_select')))

    def test_purchase_upload_bill_without_selection_raises(self):
        purchase_order = self._create_confirmed_purchase_order()
        with self.assertRaises(UserError):
            purchase_order._action_upload_bill_selected()
