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
from datetime import timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import SalonCommon


@tagged('post_install', '-at_install')
class TestSalonOrder(SalonCommon):

    # ------------------------------------------------------------------
    # creation / computed fields
    # ------------------------------------------------------------------
    def test_create_defaults(self):
        order = self.make_order()
        self.assertEqual(order.name, 'Draft Salon Order')
        self.assertEqual(order.stage_id, self.stage_draft)
        self.assertEqual(order.salon_order_created_user, self.env.uid)
        self.assertEqual(order.currency_id,
                         self.env.company.currency_id)

    def test_totals_and_end_time(self):
        order = self.make_order()
        self.assertEqual(order.price_subtotal, 150.0)
        self.assertEqual(order.time_taken_total, 1.5)
        self.assertEqual(order.end_time, self.at(hours=1.5))

    def test_totals_follow_line_changes(self):
        order = self.make_order(services=self.service_hair)
        self.assertEqual(order.price_subtotal, 100.0)
        self.env['salon.order.line'].create({
            'salon_order_id': order.id,
            'service_id': self.service_nail.id,
            'price': 50.0, 'price_subtotal': 50.0, 'time_taken': 0.5})
        self.assertEqual(order.price_subtotal, 150.0)
        self.assertEqual(order.end_time, self.at(hours=1.5))

    def test_action_update_total(self):
        order = self.make_order()
        order.price_subtotal = 0
        order.action_update_total()
        self.assertEqual(order.price_subtotal, 150.0)

    def test_read_group_stage_ids(self):
        order = self.make_order()
        stages = order._read_group_stage_ids(self.env['salon.stage'], [])
        self.assertEqual(stages, self.env['salon.stage'].search([]))

    def test_onchange_chair_from_context(self):
        order = self.env['salon.order'].with_context(
            active_id=self.chair2.id).new({})
        order._onchange_chair_id()
        self.assertEqual(order.chair_id, self.chair2)

    def test_onchange_chair_without_context(self):
        order = self.env['salon.order'].new({'chair_id': self.chair.id})
        order._onchange_chair_id()
        self.assertEqual(order.chair_id, self.chair)

    # ------------------------------------------------------------------
    # order lines
    # ------------------------------------------------------------------
    def test_line_onchange_service(self):
        line = self.env['salon.order.line'].new(
            {'service_id': self.service_hair.id})
        line._onchange_service_id()
        self.assertEqual(line.price, 100.0)
        self.assertEqual(line.price_subtotal, 100.0)
        self.assertEqual(line.time_taken, 1.0)

    def test_line_onchange_price_and_subtotal(self):
        line = self.env['salon.order.line'].new({'price': 75.0})
        line._onchange_price()
        self.assertEqual(line.price_subtotal, 75.0)
        line.price_subtotal = 60.0
        line._onchange_price_subtotal()
        self.assertEqual(line.price, 60.0)

    def test_line_deleted_with_order(self):
        order = self.make_order()
        lines = order.order_line_ids
        order.unlink()
        self.assertFalse(lines.exists())

    # ------------------------------------------------------------------
    # chair double-booking constraint
    # ------------------------------------------------------------------
    def test_same_start_time_same_chair_rejected(self):
        self.make_order()
        with self.assertRaises(ValidationError):
            self.make_order()

    def test_overlapping_order_rejected(self):
        self.make_order()  # 09:00 - 10:30
        with self.assertRaises(ValidationError):
            self.make_order(start=self.at(hours=1))

    def test_adjacent_orders_allowed(self):
        self.make_order()  # 09:00 - 10:30
        other = self.make_order(start=self.at(hours=1.5))
        self.assertTrue(other.id)

    def test_other_chair_allowed(self):
        self.make_order()
        other = self.make_order(chair=self.chair2)
        self.assertTrue(other.id)

    def test_cancelled_order_frees_the_chair(self):
        first = self.make_order()
        first.action_cancel()
        again = self.make_order()
        self.assertTrue(again.id)

    def test_get_conflicting_orders(self):
        first = self.make_order()
        # an order never conflicts with itself
        self.assertFalse(first._get_conflicting_orders())
        # an order on another chair at the same time does not conflict
        other = self.make_order(chair=self.chair2)
        self.assertFalse(other._get_conflicting_orders())
        self.assertEqual(first._get_cancelled_stage_id(),
                         self.stage_cancel.id)

    def test_cancelled_stage_lookup_ignores_renaming(self):
        """Stages are found by XML id, so renaming/translating one is safe."""
        self.stage_cancel.name = 'Something else'
        self.assertEqual(self.env['salon.order']._get_cancelled_stage_id(),
                         self.stage_cancel.id)

    def test_cancelled_stage_lookup_without_stage(self):
        self.env['ir.model.data'].search([
            ('module', '=', 'salon_management'),
            ('name', '=', 'salon_stage_04'),
        ]).unlink()
        self.assertFalse(self.env['salon.order']._get_cancelled_stage_id())

    # ------------------------------------------------------------------
    # workflow
    # ------------------------------------------------------------------
    def test_validate_then_confirm(self):
        order = self.make_order(partner_id=self.customer.id)
        order.action_validate()
        self.assertTrue(order.validation_controller)
        order.action_confirm()
        self.assertEqual(order.stage_id, self.stage_open)
        self.assertTrue(order.name.startswith('SALON/'))
        self.assertTrue(self.customer.partner_salon)
        self.assertEqual(self.chair.total_time_taken_chair, 1.5)

    def test_confirm_assigns_chair_user(self):
        user = self.env['res.users'].create(
            {'name': 'Chair Stylist', 'login': 'chair_stylist'})
        chair = self.env['salon.chair'].create({
            'date': self.at(),
            'user_line': [(0, 0, {'user_id': user.id,
                                  'start_date': self.at()})]})
        order = self.make_order(chair=chair)
        order.action_confirm()
        self.assertEqual(order.user_id, user)

    def test_drag_draft_to_open_confirms(self):
        order = self.make_order()
        order.write({'stage_id': self.stage_open.id})
        self.assertEqual(order.stage_id, self.stage_open)
        self.assertNotEqual(order.name, 'Draft Salon Order')
        self.assertTrue(order.validation_controller)

    def test_sequence_increments(self):
        first = self.make_order()
        second = self.make_order(start=self.at(days=1))
        first.action_confirm()
        second.action_confirm()
        self.assertNotEqual(first.name, second.name)

    def test_cancel_draft(self):
        order = self.make_order()
        order.action_cancel()
        self.assertEqual(order.stage_id, self.stage_cancel)

    def test_cancel_open_releases_chair_time(self):
        order = self.make_order()
        order.action_confirm()
        self.assertEqual(self.chair.total_time_taken_chair, 1.5)
        order.action_cancel()
        self.assertEqual(order.stage_id, self.stage_cancel)
        self.assertEqual(self.chair.total_time_taken_chair, 0.0)

    def test_invalid_moves_from_draft(self):
        order = self.make_order()
        for stage in (self.stage_invoiced, self.stage_closed):
            with self.assertRaises(ValidationError):
                order.write({'stage_id': stage.id})

    def test_invalid_moves_from_open(self):
        order = self.make_order()
        order.action_confirm()
        for stage in (self.stage_draft, self.stage_closed):
            with self.assertRaises(ValidationError):
                order.write({'stage_id': stage.id})

    def test_close_from_open_not_allowed(self):
        order = self.make_order()
        order.action_confirm()
        with self.assertRaises(ValidationError):
            order.action_close()

    def test_close_from_invoiced(self):
        order = self.make_order()
        order.action_confirm()
        order.action_create_invoice()
        order.action_close()
        self.assertEqual(order.stage_id, self.stage_closed)

    def test_write_on_multiple_orders(self):
        """write() must work on several records (list mass-edit)."""
        order1 = self.make_order()
        order2 = self.make_order(start=self.BASE_TIME + timedelta(days=3))
        (order1 | order2).write({'note': 'bulk'})
        self.assertEqual((order1 | order2).mapped('note'), ['bulk', 'bulk'])

    def test_stage_code(self):
        order = self.make_order()
        self.assertEqual(order.stage_code, 'draft')
        order.action_confirm()
        self.assertEqual(order.stage_code, 'open')

    def test_cancelled_order_is_final(self):
        order = self.make_order()
        order.action_cancel()
        with self.assertRaises(ValidationError):
            order.write({'stage_id': self.stage_open.id})

    def test_closed_order_is_final(self):
        order = self.make_order()
        order.action_confirm()
        order.action_create_invoice()
        order.action_close()
        self.assertEqual(order.stage_id, self.stage_closed)
        with self.assertRaises(ValidationError):
            order.write({'stage_id': self.stage_cancel.id})

    def test_invoiced_only_moves_to_closed(self):
        order = self.make_order()
        order.action_confirm()
        order.action_create_invoice()
        with self.assertRaises(ValidationError):
            order.write({'stage_id': self.stage_open.id})
        order.write({'stage_id': self.stage_closed.id})
        self.assertEqual(order.stage_id, self.stage_closed)

    def test_close_releases_chair_time(self):
        order = self.make_order()
        order.action_confirm()
        order.action_create_invoice()
        order.action_close()
        self.assertEqual(self.chair.total_time_taken_chair, 0.0)

    # ------------------------------------------------------------------
    # invoicing
    # ------------------------------------------------------------------
    def test_create_invoice_with_customer(self):
        order = self.make_order(partner_id=self.customer.id)
        order.action_confirm()
        action = order.action_create_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(action['res_model'], 'account.move')
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(invoice.partner_id, self.customer)
        self.assertEqual(invoice.invoice_origin, order.name)
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        self.assertEqual(sum(invoice.invoice_line_ids.mapped('price_unit')),
                         150.0)
        self.assertEqual(order.stage_id, self.stage_invoiced)
        self.assertTrue(order.inv_stage_identifier)
        self.assertEqual(order.count, 1)

    def test_create_invoice_default_customer(self):
        order = self.make_order()
        order.action_confirm()
        action = order.action_create_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.partner_id.name, 'Salon Default Customer')

    def test_drag_open_to_invoiced_creates_invoice(self):
        order = self.make_order(partner_id=self.customer.id)
        order.action_confirm()
        order.write({'stage_id': self.stage_invoiced.id})
        self.assertEqual(order.stage_id, self.stage_invoiced)
        self.assertEqual(order.count, 1)

    def test_invoice_updates_collection(self):
        order = self.make_order()
        order.action_confirm()
        order.action_create_invoice()
        self.assertEqual(self.chair.collection_today, 150.0)

    def test_invoice_without_default_customer(self):
        """The default customer is resolved by XML id only."""
        self.env.ref('salon_management.res_partner_01').unlink()
        order = self.make_order()
        order.action_confirm()
        with self.assertRaises(UserError):
            order.action_create_invoice()

    def test_invoice_without_service_product(self):
        self.env['ir.model.data'].search([
            ('module', '=', 'salon_management'),
            ('name', '=', 'salon_service_product_01'),
        ]).unlink()
        order = self.make_order(partner_id=self.customer.id)
        order.action_confirm()
        with self.assertRaises(UserError):
            order.action_create_invoice()

    def test_invoice_without_income_account(self):
        self.salon_product.property_account_income_id = False
        self.salon_product.categ_id.property_account_income_categ_id = False
        order = self.make_order()
        order.action_confirm()
        with self.assertRaises(UserError):
            order.action_create_invoice()

    def test_invoice_uses_category_account(self):
        self.salon_product.property_account_income_id = False
        self.salon_product.categ_id.property_account_income_categ_id = (
            self.revenue_account)
        order = self.make_order()
        order.action_confirm()
        action = order.action_create_invoice()
        self.assertTrue(action['res_id'])

    def test_action_view_invoice(self):
        order = self.make_order()
        order.action_confirm()
        order.action_create_invoice()
        action = order.action_view_invoice_salon()
        self.assertEqual(action['res_model'], 'account.move')
        self.assertEqual(action['domain'],
                         [('invoice_origin', '=', order.name)])

    # ------------------------------------------------------------------
    # deletion
    # ------------------------------------------------------------------
    def test_unlink_draft_ok(self):
        order = self.make_order()
        order.unlink()
        self.assertFalse(order.exists())

    def test_unlink_invoiced_and_closed_blocked(self):
        order = self.make_order()
        order.action_confirm()
        order.action_create_invoice()
        with self.assertRaises(UserError):
            order.unlink()
        order.action_close()
        with self.assertRaises(UserError):
            order.unlink()
