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


@tagged('post_install', '-at_install')
class TestSaleOrderCreate(TransactionCase):
    """Test cases for the overridden create() method on SaleOrder and the
    action_print_invoice() method."""

    def setUp(self):
        super().setUp()
        # Disable all automation flags before each test
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('automate_sale', False)
        params.set_param('automate_invoice', False)
        params.set_param('automate_validate_invoice', False)
        params.set_param('automate_print_invoices', False)

        # Avoid redirecting to layout configuration wizard during report_action
        layout = self.env.ref('web.external_layout_standard', raise_if_not_found=False)
        if layout:
            self.env.company.external_report_layout_id = layout

        self.partner = self.env['res.partner'].create({'name': 'Test Customer'})
        self.product_ordered = self.env['product.product'].create({
            'name': 'Ordered Product',
            'invoice_policy': 'order',
            'type': 'consu',
            'list_price': 100.0,
        })
        self.product_delivery = self.env['product.product'].create({
            'name': 'Delivery Product',
            'invoice_policy': 'delivery',
            'type': 'consu',
            'list_price': 50.0,
        })

    def _make_sale_vals(self, product):
        """Helper: build minimal sale order vals."""
        return {
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_template_id': product.product_tmpl_id.id,
                'product_uom_qty': 1,
                'price_unit': product.list_price,
            })],
        }

    def test_print_invoices_flag_set_on_create_when_enabled(self):
        """When automate_print_invoices is True, created SO should have
        automate_print_invoices=True."""
        self.env['ir.config_parameter'].sudo().set_param(
            'automate_print_invoices', True)
        order = self.env['sale.order'].create(
            self._make_sale_vals(self.product_ordered))
        self.assertTrue(order.automate_print_invoices)

    def test_print_invoices_flag_not_set_when_disabled(self):
        """When automate_print_invoices is False, created SO should have
        automate_print_invoices=False."""
        order = self.env['sale.order'].create(
            self._make_sale_vals(self.product_ordered))
        self.assertFalse(order.automate_print_invoices)

    def test_sale_order_auto_confirmed_when_flag_enabled(self):
        """When automate_sale is True, a new SO should be auto-confirmed
        (state == 'sale')."""
        self.env['ir.config_parameter'].sudo().set_param('automate_sale', True)
        order = self.env['sale.order'].create(
            self._make_sale_vals(self.product_ordered))
        self.assertEqual(order.state, 'sale',
                         "Sale order should be auto-confirmed.")

    def test_sale_order_not_auto_confirmed_when_flag_disabled(self):
        """When automate_sale is False, a new SO should remain in draft."""
        order = self.env['sale.order'].create(
            self._make_sale_vals(self.product_ordered))
        self.assertEqual(order.state, 'draft',
                         "Sale order should stay in draft without automation.")

    def test_website_order_not_auto_confirmed(self):
        """Orders originating from website (website_id set) must NOT be
        auto-confirmed even when automate_sale is enabled."""
        self.env['ir.config_parameter'].sudo().set_param('automate_sale', True)
        website = self.env['website'].search([], limit=1)
        if not website:
            self.skipTest("No website record found; skipping website_id test.")
        vals = self._make_sale_vals(self.product_ordered)
        vals['website_id'] = website.id
        order = self.env['sale.order'].create(vals)
        self.assertNotEqual(order.state, 'sale',
                            "Website orders should not be auto-confirmed.")

    def test_invoice_created_when_automate_invoice_enabled(self):
        """When automate_sale + automate_invoice are True, an invoice should
        be created automatically on SO creation."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('automate_sale', True)
        params.set_param('automate_invoice', True)
        order = self.env['sale.order'].create(
            self._make_sale_vals(self.product_ordered))
        self.assertTrue(order.invoice_ids,
                        "An invoice should have been auto-created.")

    def test_no_invoice_when_only_automate_sale_enabled(self):
        """When only automate_sale is True (not automate_invoice), no invoice
        should be created."""
        self.env['ir.config_parameter'].sudo().set_param('automate_sale', True)
        order = self.env['sale.order'].create(
            self._make_sale_vals(self.product_ordered))
        self.assertFalse(order.invoice_ids,
                         "No invoice should be created without automate_invoice.")

    def test_delivery_policy_raises_validation_error_on_invoice(self):
        """Using a product with invoice_policy='delivery' when automate_invoice
        is enabled should raise a ValidationError."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('automate_sale', True)
        params.set_param('automate_invoice', True)
        with self.assertRaises(ValidationError):
            self.env['sale.order'].create(
                self._make_sale_vals(self.product_delivery))

    def test_invoice_validated_when_all_flags_enabled(self):
        """When automate_sale + automate_invoice + automate_validate_invoice
        are all True, the created invoice should be in state 'posted'."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('automate_sale', True)
        params.set_param('automate_invoice', True)
        params.set_param('automate_validate_invoice', True)
        order = self.env['sale.order'].create(
            self._make_sale_vals(self.product_ordered))
        self.assertTrue(order.invoice_ids)
        for inv in order.invoice_ids:
            self.assertEqual(inv.state, 'posted',
                             "Invoice should be auto-validated (posted).")

    def test_invoice_remains_draft_without_validate_flag(self):
        """When automate_validate_invoice is False, the auto-created invoice
        should remain in draft/state != posted."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('automate_sale', True)
        params.set_param('automate_invoice', True)
        order = self.env['sale.order'].create(
            self._make_sale_vals(self.product_ordered))
        for inv in order.invoice_ids:
            self.assertNotEqual(inv.state, 'posted',
                                "Invoice should NOT be auto-posted.")

    def test_action_print_invoice_returns_action(self):
        """action_print_invoice() should return a report action dict."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('automate_sale', True)
        params.set_param('automate_invoice', True)
        params.set_param('automate_validate_invoice', True)
        order = self.env['sale.order'].create(
            self._make_sale_vals(self.product_ordered))
        result = order.action_print_invoice()
        self.assertIsInstance(result, dict)
        self.assertIn('type', result)
        self.assertEqual(result.get('type'), 'ir.actions.report')

    def test_action_print_invoice_field_default_false(self):
        """automate_print_invoices field on sale.order should default to False."""
        order = self.env['sale.order'].create(
            self._make_sale_vals(self.product_ordered))
        self.assertFalse(order.automate_print_invoices)


@tagged('post_install', '-at_install')
class TestSaleOrderField(TransactionCase):
    """Unit tests for the new field added to sale.order."""

    def test_automate_print_invoices_field_is_boolean(self):
        """automate_print_invoices on sale.order must be a Boolean field."""
        field = self.env['sale.order']._fields.get('automate_print_invoices')
        self.assertIsNotNone(field, "Field automate_print_invoices not found.")
        from odoo import fields as odoo_fields
        self.assertIsInstance(field, odoo_fields.Boolean)

    def test_automate_print_invoices_string_label(self):
        """automate_print_invoices label should be 'Print Invoices'."""
        field = self.env['sale.order']._fields.get('automate_print_invoices')
        self.assertEqual(field.string, 'Print Invoices')


@tagged('post_install', '-at_install')
class TestSaleOrderIntegration(TransactionCase):
    """End-to-end integration tests covering sale order automation flow."""

    def setUp(self):
        super().setUp()
        params = self.env['ir.config_parameter'].sudo()
        for key in ('automate_sale', 'automate_invoice',
                    'automate_validate_invoice', 'automate_print_invoices'):
            params.set_param(key, False)

        self.partner = self.env['res.partner'].create({'name': 'Integration Partner'})
        self.product = self.env['product.product'].create({
            'name': 'Integration Product',
            'invoice_policy': 'order',
            'type': 'consu',
            'list_price': 200.0,
        })

    def _so_vals(self):
        return {
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_template_id': self.product.product_tmpl_id.id,
                'product_uom_qty': 2,
                'price_unit': self.product.list_price,
            })],
        }

    def test_full_sale_automation_flow(self):
        """Full automation: SO created → confirmed → invoice created → posted."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('automate_sale', True)
        params.set_param('automate_invoice', True)
        params.set_param('automate_validate_invoice', True)
        params.set_param('automate_print_invoices', True)

        order = self.env['sale.order'].create(self._so_vals())

        self.assertEqual(order.state, 'sale', "SO must be confirmed.")
        self.assertTrue(order.invoice_ids, "Invoice must be created.")
        for inv in order.invoice_ids:
            self.assertEqual(inv.state, 'posted', "Invoice must be posted.")
        self.assertTrue(order.automate_print_invoices,
                        "Print invoices flag must be set.")

    def test_partial_sale_automation_confirm_only(self):
        """Only automate_sale: SO confirmed, no invoice."""
        self.env['ir.config_parameter'].sudo().set_param('automate_sale', True)
        order = self.env['sale.order'].create(self._so_vals())
        self.assertEqual(order.state, 'sale')
        self.assertFalse(order.invoice_ids)

    def test_no_automation_sale_order(self):
        """With no flags set, SO should be draft with no invoice."""
        order = self.env['sale.order'].create(self._so_vals())
        self.assertEqual(order.state, 'draft')
        self.assertFalse(order.invoice_ids)
        self.assertFalse(order.automate_print_invoices)
