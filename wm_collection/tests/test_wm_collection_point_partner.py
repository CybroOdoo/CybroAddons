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
import logging

from odoo.tests import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_collection')
class TestWmCollectionPointPartner(TransactionCase):
    """Unit tests verifying collection point address synchronization with partner records."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Partner One',
            'street': '123 Main St',
            'city': 'Green City',
            'zip': '12345',
        })
        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'Partner Two',
            'street': '456 Side St',
            'city': 'Blue City',
            'zip': '67890',
        })

        cls.point_1 = cls.env['wm.collection.point'].create({
            'name': 'Point One',
            'partner_id': cls.partner_1.id,
        })
        cls.point_2 = cls.env['wm.collection.point'].create({
            'name': 'Point Two',
            'partner_id': cls.partner_2.id,
        })

    def test_onchange_partner_id_auto_selects_single_point(self):
        """
        Test that onchange partner id auto selects single point behaves as
        expected.
        """
        order = self.env['wm.collection.order'].new({'partner_id': self.partner_1.id})
        order._onchange_partner_id()
        self.assertEqual(order.collection_point_id, self.point_1, "Should auto-select single collection point for partner")

    def test_onchange_partner_id_clears_mismatched_point(self):
        """
        Test that onchange partner id clears mismatched point behaves as
        expected.
        """
        order = self.env['wm.collection.order'].new({
            'partner_id': self.partner_1.id,
            'collection_point_id': self.point_1.id,
        })
        order.partner_id = self.partner_2
        order._onchange_partner_id()
        self.assertEqual(order.collection_point_id, self.point_2, "Should change point to partner 2 point")

    def test_collection_point_address_onchange(self):
        """
        Test that collection point address onchange behaves as expected.
        """
        point = self.env['wm.collection.point'].new({'partner_id': self.partner_1.id})
        point._onchange_partner_id()
        self.assertEqual(point.street, self.partner_1.street, "Street should auto-fill from partner")
        self.assertEqual(point.city, self.partner_1.city, "City should auto-fill from partner")

    def test_assign_route_adds_collection_point_to_route_lines(self):
        """
        Test that assign route adds collection point to route lines behaves as
        expected.
        """
        route = self.env['wm.route'].create({'name': 'Test Route 1'})
        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner_1.id,
            'collection_point_id': self.point_1.id,
        })
        self.assertNotIn(self.point_1, route.line_ids.mapped('collection_point_id'))

        order.write({'route_id': route.id})
        self.assertIn(self.point_1, route.line_ids.mapped('collection_point_id'), "Assigning route to order should add its collection point to route lines")

    def test_create_order_with_route_adds_collection_point(self):
        """
        Test that create order with route adds collection point behaves as
        expected.
        """
        route = self.env['wm.route'].create({'name': 'Test Route 2'})
        self.env['wm.collection.order'].create({
            'partner_id': self.partner_2.id,
            'collection_point_id': self.point_2.id,
            'route_id': route.id,
        })
        self.assertIn(self.point_2, route.line_ids.mapped('collection_point_id'), "Creating order with route should add collection point to route lines")

    def test_assign_route_does_not_duplicate_existing_collection_point(self):
        """
        Test that assign route does not duplicate existing collection point
        behaves as expected.
        """
        route = self.env['wm.route'].create({'name': 'Test Route 3'})
        self.env['wm.collection.order'].create({
            'partner_id': self.partner_1.id,
            'collection_point_id': self.point_1.id,
            'route_id': route.id,
        })
        self.env['wm.collection.order'].create({
            'partner_id': self.partner_1.id,
            'collection_point_id': self.point_1.id,
            'route_id': route.id,
        })
        matching_lines = route.line_ids.filtered(lambda l: l.collection_point_id == self.point_1)
        self.assertEqual(len(matching_lines), 1, "Should not duplicate collection point line in route")
