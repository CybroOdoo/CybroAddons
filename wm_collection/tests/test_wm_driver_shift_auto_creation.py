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

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestWMDriverShiftAutoCreation(TransactionCase):
    """Unit tests verifying driver shift auto-creation and hours calculation from route start/complete."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = cls.env['res.partner'].create({'name': 'Driver Test Shift Partner'})
        cls.partner = cls.env['res.partner'].create({'name': 'Shift Customer'})
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Shift Point 1',
            'partner_id': cls.partner.id,
        })
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Shift Brand'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'Shift Truck', 'brand_id': brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'license_plate': 'SHIFT-TRUCK-01',
            'model_id': model.id,
            'driver_id': cls.driver.id,
        })
        cls.route = cls.env['wm.route'].create({
            'name': 'Shift Automated Route',
            'date': fields.Date.today(),
            'vehicle_id': cls.vehicle.id,
            'driver_id': cls.driver.id,
            'state': 'to_start',
        })
        cls.env['wm.route.line'].create({
            'route_id': cls.route.id,
            'collection_point_id': cls.point.id,
            'sequence': 10,
        })
        cls.env['wm.vehicle.maintenance.checklist'].create({
            'name': 'PRE-TRIP-SHIFT-TEST',
            'vehicle_id': cls.vehicle.id,
            'checklist_type': 'pre_trip',
            'state': 'checked',
        })

    def test_driver_shift_auto_created_on_route_start_and_closed_on_complete(self):
        """Test that starting a route creates a Driver Shift record and completing it closes the shift."""
        self.assertFalse(self.route.shift_id, "Route should not have a driver shift initially.")
        self.assertFalse(self.route.actual_start, "Route should not have actual start initially.")

        # Dispatch route
        self.route.action_dispatch_route()
        self.assertEqual(self.route.state, 'dispatched')

        # Start route
        self.route.action_start_route()
        self.assertEqual(self.route.state, 'running')
        self.assertTrue(self.route.actual_start, "Actual start datetime must be set on route start.")
        self.assertTrue(self.route.shift_id, "Driver shift must be auto-created on route start.")

        shift = self.route.shift_id
        self.assertEqual(shift.driver_id.id, self.driver.id, "Shift driver must match route driver.")
        self.assertEqual(shift.vehicle_id.id, self.vehicle.id, "Shift vehicle must match route vehicle.")
        self.assertFalse(shift.shift_end, "Shift end should be empty while route is running.")

        # Complete order linked to route
        order = self.env['wm.collection.order'].search([('route_id', '=', self.route.id)], limit=1)
        if order:
            order.with_context(programmatic_state_change=True).write({'state': 'completed'})

        # Complete route
        self.route.action_complete_route()
        self.assertEqual(self.route.state, 'completed')
        self.assertTrue(self.route.actual_end, "Actual end datetime must be set on route completion.")
        self.assertTrue(shift.shift_end, "Shift end datetime must be recorded when route completes.")
        self.assertGreaterEqual(shift.hours_driven, 0.0, "Hours driven must be calculated.")
        _logger.info("PASS: test_driver_shift_auto_created_on_route_start_and_closed_on_complete")

    def test_driver_shift_onchange_vehicle_assigns_driver(self):
        """Test that selecting a vehicle automatically assigns that vehicle's driver."""
        shift = self.env['wm.driver.shift'].new({
            'shift_start': fields.Datetime.now(),
        })
        self.assertFalse(shift.vehicle_id)
        self.assertFalse(shift.driver_id)

        # Assign vehicle that has a driver
        shift.vehicle_id = self.vehicle
        shift._onchange_vehicle_id()
        self.assertEqual(shift.driver_id.id, self.vehicle.driver_id.id, "Driver should be auto-assigned from vehicle onchange.")

        # Clear vehicle
        shift.vehicle_id = False
        shift._onchange_vehicle_id()
        self.assertFalse(shift.driver_id, "Driver should be cleared when vehicle is removed.")
        _logger.info("PASS: test_driver_shift_onchange_vehicle_assigns_driver")
