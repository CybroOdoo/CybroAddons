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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, TransactionCase, tagged

GROUP_XML_ID = (
    'cancel_mrp_order.cancel_mrp_order_group_cancel_manufacturing_order')


@tagged('post_install', '-at_install')
class TestCancelMrpOrder(TransactionCase):
    """Test cancelling done manufacturing orders and the stock reversal."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.finished_product = cls._create_product('Cancel MO Finished')
        cls.component = cls._create_product('Cancel MO Component')
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.finished_product.product_tmpl_id.id,
            'product_qty': 1.0,
            'bom_line_ids': [Command.create({
                'product_id': cls.component.id,
                'product_qty': 2.0,
            })],
        })
        cls._set_stock(cls.component, 100.0)
        cls.cancel_group = cls.env.ref(GROUP_XML_ID)
        cls.env.user.group_ids = [Command.link(cls.cancel_group.id)]

    @classmethod
    def _create_product(cls, name):
        """Create a storable product."""
        return cls.env['product.product'].create({
            'name': name,
            'type': 'consu',
            'is_storable': True,
        })

    @classmethod
    def _set_stock(cls, product, quantity):
        """Put the given quantity of the product in the stock location."""
        cls.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': product.id,
            'location_id': cls.stock_location.id,
            'inventory_quantity': quantity,
        }).action_apply_inventory()

    def _get_quantity(self, product, location):
        """Return the on-hand quantity of the product in the location."""
        quants = self.env['stock.quant'].search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id),
        ])
        return sum(quants.mapped('quantity'))

    def _create_done_order(self, quantity=3.0):
        """Create, confirm and produce a manufacturing order."""
        mo_form = Form(self.env['mrp.production'])
        mo_form.product_id = self.finished_product
        mo_form.bom_id = self.bom
        mo_form.product_qty = quantity
        order = mo_form.save()
        order.action_confirm()
        order.action_assign()
        mo_form = Form(order)
        mo_form.qty_producing = quantity
        order = mo_form.save()
        order.button_mark_done()
        self.assertEqual(order.state, 'done')
        return order

    def test_cancel_done_order_sets_cancel_state(self):
        """Cancelling a done order moves the order to cancel."""
        order = self._create_done_order()
        order.action_cancel_manufacturing_order()
        self.assertEqual(order.state, 'cancel')

    def test_cancel_removes_finished_product_from_stock(self):
        """The produced quantity is taken out of the destination location."""
        order = self._create_done_order(quantity=3.0)
        destination = order.move_finished_ids.location_dest_id
        self.assertEqual(self._get_quantity(self.finished_product, destination), 3.0)
        order.action_cancel_manufacturing_order()
        self.assertEqual(self._get_quantity(self.finished_product, destination), 0.0)

    def test_cancel_returns_components_to_stock(self):
        """The consumed components are put back in the source location."""
        order = self._create_done_order(quantity=3.0)
        self.assertEqual(self._get_quantity(self.component, self.stock_location), 94.0)
        order.action_cancel_manufacturing_order()
        self.assertEqual(self._get_quantity(self.component, self.stock_location), 100.0)

    def test_cancel_cancels_work_orders(self):
        """The work orders of the cancelled order are set to cancel."""
        self.env.user.group_ids = [
            Command.link(self.env.ref('mrp.group_mrp_routings').id)]
        workcenter = self.env['mrp.workcenter'].create({'name': 'Cancel MO Center'})
        self.bom.write({'operation_ids': [Command.create({
            'name': 'Cancel MO Operation',
            'workcenter_id': workcenter.id,
        })]})
        order = self._create_done_order()
        self.assertTrue(order.workorder_ids)
        order.action_cancel_manufacturing_order()
        self.assertEqual(set(order.workorder_ids.mapped('state')), {'cancel'})

    def test_cancel_rejects_order_not_done(self):
        """An order that is not done cannot be cancelled."""
        mo_form = Form(self.env['mrp.production'])
        mo_form.product_id = self.finished_product
        mo_form.bom_id = self.bom
        order = mo_form.save()
        order.action_confirm()
        with self.assertRaises(UserError):
            order.action_cancel_manufacturing_order()
        self.assertEqual(order.state, 'confirmed')

    def test_cancel_requires_group(self):
        """A user outside the cancel group cannot call the method."""
        order = self._create_done_order()
        self.env.user.group_ids = [Command.unlink(self.cancel_group.id)]
        with self.assertRaises(AccessError):
            order.action_cancel_manufacturing_order()

    def test_server_action_cancels_selected_orders(self):
        """The Action menu entry cancels every selected done order."""
        orders = self._create_done_order() | self._create_done_order(2.0)
        action = self.env.ref('cancel_mrp_order.action_production_order_cancel')
        action.with_context(
            active_model='mrp.production',
            active_ids=orders.ids,
            active_id=orders[0].id,
        ).run()
        self.assertEqual(set(orders.mapped('state')), {'cancel'})

    def test_server_action_is_restricted_to_group(self):
        """The Action menu entry is limited to the cancel group."""
        action = self.env.ref('cancel_mrp_order.action_production_order_cancel')
        self.assertIn(self.cancel_group, action.group_ids)

    def test_form_view_contains_cancel_button(self):
        """A user of the cancel group sees the cancel button on the form."""
        arch = self.env['mrp.production'].get_view(view_type='form')['arch']
        self.assertIn('action_cancel_manufacturing_order', arch)

    def test_form_view_hides_cancel_button_without_group(self):
        """A user outside the cancel group does not see the cancel button."""
        self.env.user.group_ids = [Command.unlink(self.cancel_group.id)]
        arch = self.env['mrp.production'].get_view(view_type='form')['arch']
        self.assertNotIn('action_cancel_manufacturing_order', arch)
