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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from unittest.mock import patch

from odoo.fields import Command
from odoo.tests import new_test_user, tagged

from odoo.addons.sale.tests.common import TestSaleCommon
from odoo.addons.stock.models.stock_picking import \
    StockPicking as BaseStockPicking

CREATE_KEY = 'automatic_invoice_and_post.is_create_invoice_delivery_validate'
SEND_KEY = 'automatic_invoice_and_post.is_auto_send_invoice'


@tagged('post_install', '-at_install')
class TestAutomaticInvoiceAndPost(TestSaleCommon):
    """Check invoice creation, posting and sending on delivery validation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_delivery = cls._create_product(
            name='Auto Invoice Delivery Product', type='consu',
            invoice_policy='delivery', list_price=100.0, taxes_id=False)
        cls.product_order = cls._create_product(
            name='Auto Invoice Order Product', type='consu',
            invoice_policy='order', list_price=50.0, taxes_id=False)
        cls.partner_with_email = cls.env['res.partner'].create({
            'name': 'Customer With Email',
            'email': 'customer@example.com',
        })
        cls.partner_without_email = cls.env['res.partner'].create({
            'name': 'Customer Without Email',
        })

    def _set_config(self, create_invoice=False, send_invoice=False):
        """Save the module options through the settings flow."""
        self.env['res.config.settings'].create({
            'is_create_invoice_delivery_validate': create_invoice,
            'is_auto_send_invoice': send_invoice,
        }).execute()

    def _create_confirmed_order(self, partner, product, qty=2.0):
        """Create and confirm a sale order, which creates its delivery."""
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [Command.create({
                'product_id': product.id,
                'product_uom_qty': qty,
            })],
        })
        order.action_confirm()
        return order

    def _fully_validate(self, picking):
        """Set the full demand as done quantity and validate the picking."""
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        return picking.button_validate()

    # ------------------------------------------------------------------
    # res.config.settings
    # ------------------------------------------------------------------
    def test_settings_store_config_parameters(self):
        """The settings fields are persisted as config parameters."""
        param = self.env['ir.config_parameter'].sudo()
        self._set_config(create_invoice=True, send_invoice=True)
        self.assertTrue(param.get_bool(CREATE_KEY))
        self.assertTrue(param.get_bool(SEND_KEY))
        settings = self.env['res.config.settings'].create({})
        self.assertTrue(settings.is_create_invoice_delivery_validate)
        self.assertTrue(settings.is_auto_send_invoice)

        self._set_config(create_invoice=False, send_invoice=False)
        self.assertFalse(param.get_bool(CREATE_KEY))
        self.assertFalse(param.get_bool(SEND_KEY))
        settings = self.env['res.config.settings'].create({})
        self.assertFalse(settings.is_create_invoice_delivery_validate)
        self.assertFalse(settings.is_auto_send_invoice)

    # ------------------------------------------------------------------
    # stock.picking.button_validate
    # ------------------------------------------------------------------
    def test_no_invoice_when_options_disabled(self):
        """Without any option enabled no invoice is created."""
        self._set_config()
        order = self._create_confirmed_order(
            self.partner_with_email, self.product_delivery)
        res = self._fully_validate(order.picking_ids)
        self.assertTrue(res)
        self.assertEqual(order.picking_ids.state, 'done')
        self.assertFalse(order.invoice_ids)

    def test_invoice_created_and_posted(self):
        """With auto post enabled the invoice is created and posted."""
        self._set_config(create_invoice=True)
        order = self._create_confirmed_order(
            self.partner_with_email, self.product_delivery)
        self._fully_validate(order.picking_ids)
        invoice = order.invoice_ids
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.state, 'posted')
        self.assertEqual(invoice.amount_untaxed, 200.0)
        self.assertFalse(invoice.is_move_sent,
                         "The invoice must not be sent when auto send is off.")

    def test_invoice_created_for_order_policy_without_invoice(self):
        """An order-policy product is invoiced when the SO has no invoice."""
        self._set_config(create_invoice=True)
        order = self._create_confirmed_order(
            self.partner_with_email, self.product_order)
        self._fully_validate(order.picking_ids)
        self.assertEqual(len(order.invoice_ids), 1)
        self.assertEqual(order.invoice_ids.state, 'posted')

    def test_no_new_invoice_for_order_policy_already_invoiced(self):
        """An already invoiced order-policy SO is not invoiced again."""
        self._set_config(create_invoice=True)
        order = self._create_confirmed_order(
            self.partner_with_email, self.product_order)
        existing_invoice = order._create_invoices()
        self._fully_validate(order.picking_ids)
        self.assertEqual(order.invoice_ids, existing_invoice)
        self.assertEqual(existing_invoice.state, 'draft')

    def test_invoice_sent_when_partner_has_email(self):
        """With auto send enabled the posted invoice is mailed."""
        self._set_config(create_invoice=True, send_invoice=True)
        order = self._create_confirmed_order(
            self.partner_with_email, self.product_delivery)
        self._fully_validate(order.picking_ids)
        invoice = order.invoice_ids
        self.assertEqual(invoice.state, 'posted')
        self.assertTrue(invoice.is_move_sent)
        message = invoice.message_ids.filtered(
            lambda m: m.message_type == 'email' and m.attachment_ids)
        self.assertEqual(len(message), 1)
        self.assertIn(self.partner_with_email, message.partner_ids)
        self.assertEqual(message.attachment_ids.name,
                         '%s.pdf' % invoice.name.replace('/', '_'))
        self.assertEqual(message.attachment_ids.res_model, 'account.move')
        self.assertEqual(message.attachment_ids.res_id, invoice.id)
        self.assertTrue(message.attachment_ids.raw,
                        "The attachment must contain the rendered report.")

    def test_auto_send_only_does_nothing(self):
        """Auto send alone does not create, post or send any invoice."""
        self._set_config(send_invoice=True)
        order = self._create_confirmed_order(
            self.partner_with_email, self.product_delivery)
        self._fully_validate(order.picking_ids)
        self.assertEqual(order.picking_ids.state, 'done')
        self.assertFalse(order.invoice_ids)

    def test_invoice_not_sent_when_partner_has_no_email(self):
        """A partner without email does not receive the invoice."""
        self._set_config(create_invoice=True, send_invoice=True)
        order = self._create_confirmed_order(
            self.partner_without_email, self.product_delivery)
        with patch.object(type(self.env['stock.picking']),
                          '_send_invoice_email') as mock_send:
            self._fully_validate(order.picking_ids)
        mock_send.assert_not_called()
        self.assertEqual(order.invoice_ids.state, 'posted')
        self.assertFalse(order.invoice_ids.is_move_sent)

    def test_backorder_wizard_is_returned(self):
        """A partial delivery returns the backorder wizard untouched."""
        self._set_config(create_invoice=True, send_invoice=True)
        order = self._create_confirmed_order(
            self.partner_with_email, self.product_delivery, qty=5.0)
        picking = order.picking_ids
        picking.move_ids.quantity = 2.0
        res = picking.button_validate()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get('res_model'), 'stock.backorder.confirmation')
        self.assertNotEqual(picking.state, 'done')
        self.assertFalse(order.invoice_ids)

    def test_picking_without_sale_order_is_skipped(self):
        """A delivery without sale order does not create any invoice."""
        self._set_config(create_invoice=True, send_invoice=True)
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1)
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_with_email.id,
            'picking_type_id': warehouse.out_type_id.id,
            'location_id': warehouse.lot_stock_id.id,
            'location_dest_id': self.env.ref(
                'stock.stock_location_customers').id,
            'move_ids': [Command.create({
                'product_id': self.product_delivery.id,
                'product_uom_qty': 1.0,
                'location_id': warehouse.lot_stock_id.id,
                'location_dest_id': self.env.ref(
                    'stock.stock_location_customers').id,
            })],
        })
        picking.action_confirm()
        move_count = self.env['account.move'].search_count([])
        res = self._fully_validate(picking)
        self.assertTrue(res)
        self.assertEqual(picking.state, 'done')
        self.assertFalse(picking.sale_id)
        self.assertEqual(self.env['account.move'].search_count([]),
                         move_count)

    def test_no_done_pickings_returns_result(self):
        """When nothing ends up done, the super result is returned as is."""
        self._set_config(create_invoice=True)
        order = self._create_confirmed_order(
            self.partner_with_email, self.product_delivery)
        picking = order.picking_ids
        with patch.object(BaseStockPicking, 'button_validate',
                          return_value=True):
            res = picking.button_validate()
        self.assertIs(res, True)
        self.assertNotEqual(picking.state, 'done')
        self.assertFalse(order.invoice_ids)

    def test_backorder_of_invoiced_order_is_not_invoiced_again(self):
        """Validating the backorder of a fully invoiced order raises no
        error and creates no new invoice."""
        self._set_config(create_invoice=True)
        order = self._create_confirmed_order(
            self.partner_with_email, self.product_order, qty=5.0)
        picking = order.picking_ids
        picking.picking_type_id.create_backorder = 'always'
        picking.move_ids.quantity = 2.0
        picking.button_validate()
        invoice = order.invoice_ids
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.state, 'posted')
        self.assertEqual(order.invoice_status, 'invoiced')

        backorder = order.picking_ids - picking
        self.assertEqual(len(backorder), 1)
        self._fully_validate(backorder)
        self.assertEqual(backorder.state, 'done')
        self.assertEqual(order.invoice_ids, invoice)

    def test_multi_step_delivery_invoices_on_final_step(self):
        """In a pick + ship route only the outgoing step is invoiced."""
        self._set_config(create_invoice=True)
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1)
        warehouse.delivery_steps = 'pick_ship'
        order = self._create_confirmed_order(
            self.partner_with_email, self.product_delivery)
        pick = order.picking_ids
        self.assertEqual(pick.picking_type_code, 'internal')
        self.assertEqual(pick.sale_id, order,
                         "The pick step is linked to the sale order too.")

        self._fully_validate(pick)
        self.assertEqual(pick.state, 'done')
        self.assertFalse(order.invoice_ids,
                         "The pick step must not create an invoice.")

        # The ship step is created once the pick step is done.
        ship = order.picking_ids.filtered(
            lambda p: p.picking_type_code == 'outgoing')
        self.assertEqual(len(ship), 1)
        self._fully_validate(ship)
        self.assertEqual(ship.state, 'done')
        self.assertEqual(len(order.invoice_ids), 1)
        self.assertEqual(order.invoice_ids.state, 'posted')

    def test_stock_user_can_validate_delivery(self):
        """A user with only inventory rights can validate the delivery and
        the invoice is still created, posted and sent."""
        self._set_config(create_invoice=True, send_invoice=True)
        stock_user = new_test_user(
            self.env, login='auto_invoice_stock_user',
            groups='stock.group_stock_user')
        order = self._create_confirmed_order(
            self.partner_with_email, self.product_delivery)
        self._fully_validate(order.picking_ids.with_user(stock_user))
        self.assertEqual(order.picking_ids.state, 'done')
        self.assertEqual(order.invoice_ids.state, 'posted')
        self.assertTrue(order.invoice_ids.is_move_sent)

    # ------------------------------------------------------------------
    # stock.picking._send_invoice_email
    # ------------------------------------------------------------------
    def test_send_draft_invoice_with_origin(self):
        """A draft invoice uses the origin in its file name and subject."""
        order = self._create_confirmed_order(
            self.partner_with_email, self.product_order)
        invoice = order._create_invoices()
        self.assertEqual(invoice.state, 'draft')
        self.env['stock.picking']._send_invoice_email(invoice)
        self.assertTrue(invoice.is_move_sent)
        message = invoice.message_ids.filtered(
            lambda m: m.message_type == 'email' and m.attachment_ids)
        self.assertEqual(len(message), 1)
        self.assertEqual(message.attachment_ids.name,
                         'Draft_Invoice_%s.pdf' % order.name)
        self.assertEqual(
            message.subject,
            '%s Invoice (Draft) - Ref %s' % (invoice.company_id.name,
                                             order.name))

    def test_send_draft_invoice_without_origin(self):
        """A draft invoice without origin falls back to its id."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_with_email.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.product_order.id,
                'quantity': 1.0,
                'price_unit': 10.0,
                'tax_ids': False,
            })],
        })
        self.assertFalse(invoice.invoice_origin)
        self.env['stock.picking']._send_invoice_email(invoice)
        self.assertTrue(invoice.is_move_sent)
        message = invoice.message_ids.filtered(
            lambda m: m.message_type == 'email' and m.attachment_ids)
        self.assertEqual(message.attachment_ids.name,
                         'Draft_Invoice_%s.pdf' % invoice.id)
        self.assertEqual(
            message.subject,
            '%s Invoice (Draft) - Ref ' % invoice.company_id.name)

    def test_send_posted_invoice_uses_template_subject(self):
        """A posted invoice uses the mail template subject."""
        order = self._create_confirmed_order(
            self.partner_with_email, self.product_order)
        invoice = order._create_invoices()
        invoice.action_post()
        self.env['stock.picking']._send_invoice_email(invoice)
        template = self.env.ref('account.email_template_edi_invoice')
        expected_subject = template._render_field(
            'subject', invoice.ids)[invoice.id]
        message = invoice.message_ids.filtered(
            lambda m: m.message_type == 'email' and m.attachment_ids)
        self.assertEqual(message.subject, expected_subject)
        self.assertTrue(invoice.is_move_sent)

    def test_send_invoice_email_logs_errors(self):
        """A sending error is logged and rolled back, not raised."""
        order = self._create_confirmed_order(
            self.partner_with_email, self.product_order)
        invoice = order._create_invoices()
        invoice.action_post()
        report_model = type(self.env['ir.actions.report'])
        logger = 'odoo.addons.automatic_invoice_and_post.models.stock_picking'
        with patch.object(report_model, '_render_qweb_pdf',
                          side_effect=Exception('Rendering failed')), \
                self.assertLogs(logger, level='ERROR') as logs:
            self.env['stock.picking']._send_invoice_email(invoice)
        self.assertIn(invoice.display_name, logs.output[0])
        self.assertFalse(invoice.is_move_sent)
        self.assertFalse(invoice.message_ids.filtered(
            lambda m: m.message_type == 'email' and m.attachment_ids))
