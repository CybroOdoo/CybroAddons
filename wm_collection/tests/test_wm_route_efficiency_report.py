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


@tagged('post_install', '-at_install', 'wm_reporting')
class TestWmRouteEfficiencyReport(TransactionCase):
    """Unit tests verifying route distance, collection count, and duration efficiency metrics."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.point1 = cls.env['wm.collection.point'].create({'name': 'Point 1'})
        cls.point2 = cls.env['wm.collection.point'].create({'name': 'Point 2'})

        cls.route = cls.env['wm.route'].create({
            'name': 'ROUTE-EFF-001',
            'date': '2026-07-28',
            'estimated_duration': 2.0,
        })
        cls.line1 = cls.env['wm.route.line'].create({'route_id': cls.route.id, 'collection_point_id': cls.point1.id, 'sequence': 10})
        cls.line2 = cls.env['wm.route.line'].create({'route_id': cls.route.id, 'collection_point_id': cls.point2.id, 'sequence': 20})

        cls.order1 = cls.env['wm.collection.order'].create({
            'name': 'ORD-R1',
            'route_id': cls.route.id,
            'collection_point_id': cls.point1.id,
            'state': 'completed',
        })
        cls.order2 = cls.env['wm.collection.order'].create({
            'name': 'ORD-R2',
            'route_id': cls.route.id,
            'collection_point_id': cls.point2.id,
            'state': 'dispatched',
        })

    def test_route_efficiency_rate_calculation(self):
        """
        Test that route efficiency rate calculation behaves as expected.
        """
        reports = self.env['wm.route.efficiency.report'].search([('route_id', '=', self.route.id)])
        self.assertTrue(reports, "Route efficiency report row should be present")
        report = reports[0]
        self.assertEqual(report.points_planned, 2, "Points planned should be 2")
        self.assertEqual(report.orders_completed, 1, "Orders completed should be 1")
        self.assertEqual(report.completion_rate, 50.0, "Completion rate should be 50.0%")
        _logger.info('PASS: test_route_efficiency_rate_calculation')

    def test_zero_division_guard(self):
        """
        Test that zero division guard behaves as expected.
        """
        empty_route = self.env['wm.route'].create({
            'name': 'ROUTE-EMPTY',
            'date': '2026-07-28',
        })
        reports = self.env['wm.route.efficiency.report'].search([('route_id', '=', empty_route.id)])
        self.assertTrue(reports)
        self.assertEqual(reports[0].completion_rate, 0.0, "Completion rate for route with 0 planned points should safely be 0.0")
        _logger.info('PASS: test_zero_division_guard')
