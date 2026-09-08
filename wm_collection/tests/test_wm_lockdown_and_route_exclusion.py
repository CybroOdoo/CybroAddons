# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import timedelta
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'wm_collection', 'wm_lockdown')
class TestWmLockdownAndRouteExclusion(TransactionCase):
    """
    Test suite verifying:
    1. Completed routes are excluded from selection in Collection Orders.
    2. Operational fields and line items become readonly and strictly locked down
       on completed Collection Orders.
    3. Finalized Waste Batches (recycled, sold, disposed, cancel) and their lines
       cannot be modified or deleted.
    4. Completed Routes and their stops cannot be modified or deleted.
    """

    @classmethod
    def setUpClass(cls):
        """Initialize test environment for route lockdown and vehicle exclusion testing."""
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Environmental Partner',
        })

        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Lockdown Test Category',
            'code': 'LTC01',
            'price': 2.50,
            'auto_create_batches_on_collection': False,
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Lockdown Test Material',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
            'list_price': 3.0,
        })

        cls.collection_point = cls.env['wm.collection.point'].create({
            'name': 'Test Point Alpha',
            'partner_id': cls.partner.id,
            'category_ids': [(6, 0, [cls.category.id])],
        })

        # Test user without su rights to test non-su write/create/unlink enforcement
        cls.dispatcher_user = cls.env['res.users'].create({
            'name': 'Test Collection Operator User',
            'login': 'test_collection_op_user@example.com',
            'email': 'test_collection_op_user@example.com',
        })
        dispatcher_group = cls.env.ref('wm_base.group_wm_dispatcher')
        dispatcher_group.write({'user_ids': [(4, cls.dispatcher_user.id)]})

    def test_route_selection_excludes_completed_routes(self):
        """Verify that completed routes are filtered out by domain on wm.collection.order.route_id."""
        route_active = self.env['wm.route'].create({
            'name': 'Active Morning Route',
            'state': 'to_start',
        })
        route_completed = self.env['wm.route'].create({
            'name': 'Finished Morning Route',
            'state': 'completed',
        })

        # Check field domain on collection order model
        route_field = self.env['wm.collection.order']._fields['route_id']
        self.assertEqual(route_field.domain, "[('state', '!=', 'completed')]")

        # Evaluate domain against active and completed routes
        domain = [('state', '!=', 'completed'), ('id', 'in', [route_active.id, route_completed.id])]
        search_result = self.env['wm.route'].search(domain)
        self.assertIn(route_active, search_result)
        self.assertNotIn(route_completed, search_result)

    def test_completed_collection_order_lockdown(self):
        """Verify that once a collection order is completed, operational fields and lines cannot be modified."""
        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.collection_point.id,
            'scheduled_start': fields.Datetime.now(),
            'scheduled_end': fields.Datetime.now() + timedelta(hours=1),
            'order_line_ids': [(0, 0, {
                'category_id': self.category.id,
                'product_id': self.product.id,
                'weight': 120.0,
            })],
        })

        # Advance order to completed
        order.with_context(programmatic_state_change=True).write({
            'state': 'completed',
            'actual_end': fields.Datetime.now(),
        })
        self.assertEqual(order.state, 'completed')

        # Run modifications as non-superuser dispatcher
        order_as_user = order.with_user(self.dispatcher_user)

        # 1. Operational scalar fields modification must raise UserError
        for field_name, dummy_val in [
            ('scheduled_start', fields.Datetime.now() + timedelta(days=2)),
            ('estimated_weight', 999.0),
            ('confirmed_weight', 999.0),
            ('driver_photo', 'test_photo_string'),
            ('geolocation_tag', '37.7749,-122.4194'),
            ('retry_count', 5),
        ]:
            with self.assertRaises(UserError, msg=f"Modifying '{field_name}' on completed order should raise UserError"):
                order_as_user.write({field_name: dummy_val})

        # 2. Line modification must raise UserError
        order_line = order_as_user.order_line_ids[0]
        with self.assertRaises(UserError, msg="Modifying line weight on completed order should raise UserError"):
            order_line.write({'weight': 250.0})

        # 3. Line deletion must raise UserError
        with self.assertRaises(UserError, msg="Deleting line on completed order should raise UserError"):
            order_line.unlink()

        # 4. Adding a new line to completed order must raise UserError
        with self.assertRaises(UserError, msg="Adding line to completed order should raise UserError"):
            self.env['wm.collection.order.line'].with_user(self.dispatcher_user).create({
                'order_id': order.id,
                'category_id': self.category.id,
                'product_id': self.product.id,
                'weight': 50.0,
            })

        # 5. Order deletion must raise UserError
        with self.assertRaises(UserError, msg="Deleting completed order should raise UserError"):
            order_as_user.unlink()

    def test_finalized_waste_batch_lockdown(self):
        """Verify that finalized waste batches (disposed, recycled, sold, cancel) and their lines cannot be modified."""
        batch = self.env['waste.batch'].create({
            'name': 'BATCH-LOCKDOWN-001',
            'category_id': self.category.id,
            'status': 'draft',
            'line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 100.0,
            })],
        })

        # Advance batch to disposed
        batch.write({'status': 'disposed'})
        self.assertEqual(batch.status, 'disposed')

        batch_as_user = batch.with_user(self.dispatcher_user)

        # 1. Operational fields cannot be edited
        with self.assertRaises(UserError, msg="Modifying intake_weight on disposed batch should raise UserError"):
            batch_as_user.write({'intake_weight': 500.0})

        with self.assertRaises(UserError, msg="Modifying intake_notes on disposed batch should raise UserError"):
            batch_as_user.write({'intake_notes': 'New Notes'})

        # 2. Batch line cannot be edited
        batch_line = batch_as_user.line_ids[0]
        with self.assertRaises(UserError, msg="Modifying line quantity on disposed batch should raise UserError"):
            batch_line.write({'quantity': 200.0})

        # 3. Batch line cannot be deleted
        with self.assertRaises(UserError, msg="Deleting line on disposed batch should raise UserError"):
            batch_line.unlink()

        # 4. Adding new line to disposed batch must raise UserError
        with self.assertRaises(UserError, msg="Adding line to disposed batch should raise UserError"):
            self.env['waste.batch.line'].with_user(self.dispatcher_user).create({
                'batch_id': batch.id,
                'product_id': self.product.id,
                'quantity': 30.0,
            })

        # 5. Batch deletion must raise UserError
        with self.assertRaises(UserError, msg="Deleting disposed batch should raise UserError"):
            batch_as_user.unlink()

    def test_completed_route_lockdown(self):
        """Verify that completed routes and their stops cannot be modified or deleted."""
        route = self.env['wm.route'].create({
            'name': 'ROUTE-LOCKDOWN-001',
            'state': 'to_start',
            'line_ids': [(0, 0, {
                'collection_point_id': self.collection_point.id,
                'sequence': 10,
            })],
        })

        # Complete the route
        route.write({'state': 'completed'})
        self.assertEqual(route.state, 'completed')

        route_as_user = route.with_user(self.dispatcher_user)

        # 1. Modifying route operational fields must raise UserError
        with self.assertRaises(UserError, msg="Modifying line_ids on completed route should raise UserError"):
            route_as_user.write({'date': fields.Date.today() + timedelta(days=5)})

        # 2. Modifying route stop must raise UserError
        route_line = route_as_user.line_ids[0]
        with self.assertRaises(UserError, msg="Modifying stop sequence on completed route should raise UserError"):
            route_line.write({'sequence': 50})

        # 3. Deleting route stop must raise UserError
        with self.assertRaises(UserError, msg="Deleting stop on completed route should raise UserError"):
            route_line.unlink()

        # 4. Adding stop to completed route must raise UserError
        with self.assertRaises(UserError, msg="Adding stop to completed route should raise UserError"):
            self.env['wm.route.line'].with_user(self.dispatcher_user).create({
                'route_id': route.id,
                'collection_point_id': self.collection_point.id,
                'sequence': 20,
            })

        # 5. Deleting completed route must raise UserError
        with self.assertRaises(UserError, msg="Deleting completed route should raise UserError"):
            route_as_user.unlink()
