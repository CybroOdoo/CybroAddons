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

from odoo.tests import TransactionCase, tagged

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

    def test_distance_reported_after_optimization(self):
        """Optimizing a geolocated route stores its straight-line distance and the report shows it."""
        p1 = self.env['wm.collection.point'].create({'name': 'D1', 'latitude': 10.0, 'longitude': 76.0})
        p2 = self.env['wm.collection.point'].create({'name': 'D2', 'latitude': 10.1, 'longitude': 76.0})
        route = self.env['wm.route'].create({'name': 'ROUTE-DIST', 'date': '2026-07-28'})
        for i, pt in enumerate((p1, p2)):
            self.env['wm.route.line'].create({'route_id': route.id, 'collection_point_id': pt.id, 'sequence': 10 * (i + 1)})
        route.action_optimize_route()
        self.assertAlmostEqual(route.estimated_distance_km, 11.12, delta=0.1)
        self.env.flush_all()
        report = self.env['wm.route.efficiency.report'].search([('route_id', '=', route.id)])
        self.assertAlmostEqual(report.distance_km, route.estimated_distance_km, places=2)
