# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestPurchaseOrderCreate(TransactionCase):
    """Test cases for the overridden create() method on PurchaseOrder and the
    action_print_bill() method."""

    def setUp(self):
        super().setUp()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('automate_purchase', False)
        params.set_param('automate_print_bills', False)

        # Avoid redirecting to layout configuration wizard during report_action
        layout = self.env.ref('web.external_layout_standard', raise_if_not_found=False)
        if layout:
            self.env.company.external_report_layout_id = layout

        self.partner = self.env['res.partner'].create({'name': 'Test Vendor'})
        self.product_ordered = self.env['product.product'].create({
            'name': 'PO Ordered Product',
            'invoice_policy': 'order',
            'type': 'consu',
            'standard_price': 80.0,
        })
        self.product_delivery = self.env['product.product'].create({
            'name': 'PO Delivery Product',
            'invoice_policy': 'delivery',
            'type': 'consu',
            'standard_price': 40.0,
        })

    def _make_po_vals(self, product):
        """Helper: build minimal purchase order vals."""
        return {
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'name': product.name,
                'product_qty': 1,
                'price_unit': product.standard_price,
                'date_planned': fields.Datetime.now(),
            })],
        }

    def test_print_bills_flag_set_on_create_when_enabled(self):
        """When automate_purchase + automate_print_bills are True, created PO
        should have automate_print_bills=True."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('automate_purchase', True)
        params.set_param('automate_print_bills', True)
        order = self.env['purchase.order'].create(
            self._make_po_vals(self.product_ordered))
        self.assertTrue(order.automate_print_bills)

    def test_print_bills_flag_not_set_when_disabled(self):
        """When automate_purchase is False, created PO should have
        automate_print_bills=False."""
        order = self.env['purchase.order'].create(
            self._make_po_vals(self.product_ordered))
        self.assertFalse(order.automate_print_bills)

    def test_purchase_order_auto_confirmed_when_flag_enabled(self):
        """When automate_purchase is True, a new PO should be auto-confirmed
        (state == 'purchase')."""
        self.env['ir.config_parameter'].sudo().set_param(
            'automate_purchase', True)
        order = self.env['purchase.order'].create(
            self._make_po_vals(self.product_ordered))
        self.assertEqual(order.state, 'purchase',
                         "Purchase order should be auto-confirmed.")

    def test_purchase_order_not_auto_confirmed_when_flag_disabled(self):
        """When automate_purchase is False, a new PO should remain in draft."""
        order = self.env['purchase.order'].create(
            self._make_po_vals(self.product_ordered))
        self.assertEqual(order.state, 'draft',
                         "Purchase order should stay in draft without automation.")


    def test_delivery_policy_raises_validation_error_on_purchase(self):
        """Using a product with invoice_policy='delivery' when automate_purchase
        is enabled should raise a ValidationError."""
        self.env['ir.config_parameter'].sudo().set_param(
            'automate_purchase', True)
        with self.assertRaises(ValidationError):
            self.env['purchase.order'].create(
                self._make_po_vals(self.product_delivery))

    def test_ordered_policy_does_not_raise_on_purchase(self):
        """Products with invoice_policy='order' should NOT raise a
        ValidationError during auto-confirmed PO creation."""
        self.env['ir.config_parameter'].sudo().set_param(
            'automate_purchase', True)
        # Should not raise
        order = self.env['purchase.order'].create(
            self._make_po_vals(self.product_ordered))
        self.assertTrue(order)

    def test_create_with_dict_vals_list(self):
        """create() should handle a plain dict for vals_list gracefully
        (Odoo 19 normalizes this internally, but the override must not crash)."""
        self.env['ir.config_parameter'].sudo().set_param(
            'automate_purchase', True)
        order = self.env['purchase.order'].create(
            self._make_po_vals(self.product_ordered))
        self.assertTrue(order.exists())

    def test_action_print_bill_returns_action(self):
        """action_print_bill() should return a report action dict."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('automate_purchase', True)
        order = self.env['purchase.order'].create(
            self._make_po_vals(self.product_ordered))
        # Ensure there is a bill/invoice to print
        order._create_invoices() if hasattr(order, '_create_invoices') else None
        result = order.action_print_bill()
        self.assertIsInstance(result, dict)
        self.assertIn('type', result)
        self.assertEqual(result.get('type'), 'ir.actions.report')

    def test_action_print_bill_field_default_false(self):
        """automate_print_bills field on purchase.order should default to False."""
        order = self.env['purchase.order'].create(
            self._make_po_vals(self.product_ordered))
        self.assertFalse(order.automate_print_bills)


@tagged('post_install', '-at_install')
class TestPurchaseOrderField(TransactionCase):
    """Unit tests for the new field added to purchase.order."""

    def test_automate_print_bills_field_is_boolean(self):
        """automate_print_bills on purchase.order must be a Boolean field."""
        field = self.env['purchase.order']._fields.get('automate_print_bills')
        self.assertIsNotNone(field, "Field automate_print_bills not found.")
        from odoo import fields as odoo_fields
        self.assertIsInstance(field, odoo_fields.Boolean)

    def test_automate_print_bills_string_label(self):
        """automate_print_bills label should be 'Create Bills'."""
        field = self.env['purchase.order']._fields.get('automate_print_bills')
        self.assertEqual(field.string, 'Create Bills')


@tagged('post_install', '-at_install')
class TestPurchaseOrderIntegration(TransactionCase):
    """End-to-end integration tests covering purchase order automation flow."""

    def setUp(self):
        super().setUp()
        params = self.env['ir.config_parameter'].sudo()
        for key in ('automate_purchase', 'automate_print_bills'):
            params.set_param(key, False)

        self.partner = self.env['res.partner'].create({'name': 'Integration Partner'})
        self.product = self.env['product.product'].create({
            'name': 'Integration Product',
            'invoice_policy': 'order',
            'type': 'consu',
            'standard_price': 150.0,
        })

    def _po_vals(self):
        return {
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_qty': 2,
                'price_unit': self.product.standard_price,
                'date_planned': '2026-06-01 00:00:00',
            })],
        }

    def test_full_purchase_automation_flow(self):
        """Full automation: PO created → confirmed → print bills flag set."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('automate_purchase', True)
        params.set_param('automate_print_bills', True)

        order = self.env['purchase.order'].create(self._po_vals())

        self.assertEqual(order.state, 'purchase', "PO must be confirmed.")
        self.assertTrue(order.automate_print_bills,
                        "Print bills flag must be set.")

    def test_no_automation_purchase_order(self):
        """With no flags set, PO should be draft with no bills flag."""
        order = self.env['purchase.order'].create(self._po_vals())
        self.assertEqual(order.state, 'draft')
        self.assertFalse(order.automate_print_bills)
