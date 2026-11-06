# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, common, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestMrpOrderFromMultipleSaleOrder(common.TransactionCase):
    """Test the creation of manufacturing orders from sale orders."""

    @classmethod
    def setUpClass(cls):
        """Create products with a Bill of Materials and two sale orders."""
        super().setUpClass()

        # Create a partner for the sale orders
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })

        # Create products
        cls.product_1 = cls.env['product.product'].create({
            'name': 'Test Product 1',
            'type': 'consu',
        })
        cls.product_2 = cls.env['product.product'].create({
            'name': 'Test Product 2',
            'type': 'consu',
        })

        # Create Bill of Materials (BOM) to support standard Odoo MRP flow
        cls.bom_1 = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_1.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
        })
        cls.bom_2 = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_2.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
        })

        # Create draft sale orders
        cls.sale_order_1 = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                Command.create({
                    'product_id': cls.product_1.id,
                    'product_uom_qty': 10.0,
                }),
                Command.create({
                    'product_id': cls.product_2.id,
                    'product_uom_qty': 5.0,
                }),
            ]
        })

        cls.sale_order_2 = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                Command.create({
                    'product_id': cls.product_1.id,
                    'product_uom_qty': 3.0,
                }),
            ]
        })

    def test_01_create_mrp_orders_success(self):
        """Test successful creation of MRP orders from multiple sale orders"""
        orders = self.sale_order_1 | self.sale_order_2

        # Check initial counts
        self.assertEqual(self.sale_order_1.mrp_count, 0)
        self.assertEqual(self.sale_order_2.mrp_count, 0)
        self.assertFalse(self.sale_order_1.mrp_order_ids)
        self.assertFalse(self.sale_order_2.mrp_order_ids)

        # Trigger action
        orders.action_mrp_order()

        # Check that MRP productions were created
        mrp_productions = self.env['mrp.production'].search([
            ('sale_order_id', 'in', orders.ids)
        ])
        # We expect 3 MRP productions (2 for sale_order_1, 1 for sale_order_2)
        self.assertEqual(len(mrp_productions), 3)

        # Verify specific details of created MRP productions
        mrp_so_1 = mrp_productions.filtered(
            lambda mrp: mrp.sale_order_id == self.sale_order_1)
        self.assertEqual(len(mrp_so_1), 2)
        self.assertEqual(
            set(mrp_so_1.mapped('product_id')),
            {self.product_1, self.product_2}
        )
        # Check quantities
        qty_p1 = mrp_so_1.filtered(
            lambda mrp: mrp.product_id == self.product_1).product_qty
        qty_p2 = mrp_so_1.filtered(
            lambda mrp: mrp.product_id == self.product_2).product_qty
        self.assertEqual(qty_p1, 10.0)
        self.assertEqual(qty_p2, 5.0)

        mrp_so_2 = mrp_productions.filtered(
            lambda mrp: mrp.sale_order_id == self.sale_order_2)
        self.assertEqual(len(mrp_so_2), 1)
        self.assertEqual(mrp_so_2.product_id, self.product_1)
        self.assertEqual(mrp_so_2.product_qty, 3.0)

        # Verify fields on sale order records
        orders.invalidate_recordset(['mrp_count'])
        self.assertEqual(self.sale_order_1.mrp_count, 2)
        self.assertEqual(self.sale_order_2.mrp_count, 1)
        self.assertEqual(self.sale_order_1.mrp_order_ids, mrp_so_1)
        self.assertEqual(self.sale_order_2.mrp_order_ids, mrp_so_2)

    def test_02_validation_already_has_mrp(self):
        """Test validation error when sale order already has a manufacturing order"""
        # Create MRP production for sale_order_1 manually to simulate it having one
        self.env['mrp.production'].create({
            'product_id': self.product_1.id,
            'product_qty': 1.0,
            'sale_order_id': self.sale_order_1.id,
        })

        orders = self.sale_order_1 | self.sale_order_2

        with self.assertRaises(ValidationError) as context:
            orders.action_mrp_order()

        self.assertIn("already have a manufacturing order", str(context.exception))

    def test_03_validation_non_draft_state(self):
        """Test validation error when a sale order is not in draft state"""
        # Set sale_order_2 state to 'sale'
        self.sale_order_2.state = 'sale'

        orders = self.sale_order_1 | self.sale_order_2

        with self.assertRaises(ValidationError) as context:
            orders.action_mrp_order()

        self.assertIn("are not in draft state", str(context.exception))

    def test_04_validation_zero_quantity(self):
        """Test validation error when a sale order line has zero or negative quantity"""
        # Create a sale order line with 0 quantity
        self.sale_order_2.write({
            'order_line': [
                Command.create({
                    'product_id': self.product_2.id,
                    'product_uom_qty': 0.0,
                })
            ]
        })

        orders = self.sale_order_1 | self.sale_order_2

        with self.assertRaises(ValidationError) as context:
            orders.action_mrp_order()

        self.assertIn("have zero quantity", str(context.exception))

    def test_05_get_mrp_action(self):
        """Test the get_mrp() action on sale.order"""
        # Call action_mrp_order to link MRP orders
        self.sale_order_1.action_mrp_order()

        # Call get_mrp()
        action = self.sale_order_1.get_mrp()

        # Verify returned action attributes
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'mrp.production')
        self.assertEqual(action.get('view_mode'), 'list,form')
        self.assertEqual(action.get('domain'), [('sale_order_id', '=', self.sale_order_1.id)])
        self.assertEqual(action.get('context'), {'create': False})

    def test_06_services_and_products_without_bom_are_skipped(self):
        """Only the lines with a Bill of Materials are manufactured, and
        the sections and notes of the order are ignored."""
        service = self.env['product.product'].create({
            'name': 'Installation', 'type': 'service'})
        no_bom = self.env['product.product'].create({'name': 'Bought Item'})
        self.sale_order_2.write({'order_line': [
            Command.create({'product_id': service.id}),
            Command.create({'product_id': no_bom.id}),
            Command.create({'display_type': 'line_note', 'name': 'Note'}),
        ]})
        self.sale_order_2.action_mrp_order()
        production = self.sale_order_2.mrp_order_ids
        self.assertEqual(production.product_id, self.product_1)
        self.assertEqual(production.origin, self.sale_order_2.name)

    def test_07_order_without_bom_is_refused(self):
        """An order with nothing to manufacture is reported."""
        no_bom = self.env['product.product'].create({'name': 'Bought Item'})
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({'product_id': no_bom.id})],
        })
        with self.assertRaises(ValidationError) as context:
            order.action_mrp_order()
        self.assertIn('no product with a Bill of Materials',
                      str(context.exception))
        self.assertFalse(order.mrp_count)

    def test_08_nothing_is_created_when_one_order_fails(self):
        """A problem on one selected order stops the whole batch."""
        self.sale_order_2.state = 'sale'
        orders = self.sale_order_1 | self.sale_order_2
        with self.assertRaises(ValidationError):
            orders.action_mrp_order()
        self.assertFalse(self.sale_order_1.mrp_count)

    def test_09_order_line_unit_is_kept(self):
        """A line in dozens gives a manufacturing order in dozens."""
        dozen = self.env.ref('uom.product_uom_dozen')
        self.sale_order_2.order_line.write({
            'product_uom_id': dozen.id, 'product_uom_qty': 2})
        self.sale_order_2.action_mrp_order()
        production = self.sale_order_2.mrp_order_ids
        self.assertEqual(production.product_qty, 2)
        self.assertEqual(production.product_uom_id, dozen)

    def test_10_copies_are_not_linked(self):
        """Duplicates do not keep the link to the manufacturing orders."""
        self.sale_order_2.action_mrp_order()
        production = self.sale_order_2.mrp_order_ids
        self.assertFalse(self.sale_order_2.copy().mrp_order_ids)
        self.assertFalse(production.copy().sale_order_id)

    def test_11_salesperson_without_manufacturing_rights(self):
        """Sales users open orders normally, with or without manufacturing
        orders on them, and cannot create manufacturing orders."""
        self.sale_order_2.action_mrp_order()
        user = new_test_user(
            self.env, login='sale_only',
            groups='sales_team.group_sale_salesman_all_leads')
        order = self.sale_order_2.with_user(user)
        self.assertEqual(order.name, self.sale_order_2.name)
        with Form(order) as form:
            form.note = 'Checked'
        self.sale_order_1.with_user(user).read(['name', 'state'])
        with self.assertRaises(AccessError):
            self.sale_order_1.with_user(user).action_mrp_order()
        action = self.env.ref(
            'mrp_order_from_multiple_sale_order.action_mrp_order')
        self.assertIn(self.env.ref('mrp.group_mrp_user'), action.group_ids)

    def test_12_manufacturing_user_creates_orders(self):
        """A sales user with manufacturing rights runs the whole flow."""
        user = new_test_user(
            self.env, login='sale_mrp_user',
            groups='sales_team.group_sale_salesman_all_leads,'
                   'mrp.group_mrp_user')
        order = self.sale_order_2.with_user(user)
        order.action_mrp_order()
        self.assertEqual(order.mrp_count, 1)
        self.assertEqual(len(order.mrp_order_ids), 1)
