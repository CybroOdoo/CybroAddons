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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestFleetCompleteReport(common.TransactionCase):
    """Test suite for Fleet Complete Report wizard and PDF report generation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.context_today(cls.env.user)
        cls.past_start = cls.today - timedelta(days=30)
        cls.past_end = cls.today - timedelta(days=5)

        # Create vehicle states with sequence
        cls.state_active = cls.env['fleet.vehicle.state'].create({
            'name': 'Active Test State',
            'sequence': 1,
        })
        cls.state_inactive = cls.env['fleet.vehicle.state'].create({
            'name': 'Inactive Test State',
            'sequence': 2,
        })

        # Create brand, model and test partner / user
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Fleet Brand'})
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Fleet Model',
            'brand_id': cls.brand.id,
        })
        cls.driver = cls.env['res.partner'].create({
            'name': 'Test Fleet Driver',
            'email': 'driver@example.com',
        })

        # Create vehicles in different states
        cls.vehicle_1 = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'TEST-FL-01',
            'state_id': cls.state_active.id,
            'driver_id': cls.driver.id,
            'acquisition_date': cls.past_start,
            'vin_sn': 'VIN00000000001',
            'odometer_unit': 'kilometers',
        })
        cls.vehicle_2 = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'TEST-FL-02',
            'state_id': cls.state_inactive.id,
            'acquisition_date': cls.past_start,
            'vin_sn': 'VIN00000000002',
            'odometer_unit': 'kilometers',
        })

        # Create vehicle service type for contracts/services
        cls.service_type = cls.env['fleet.service.type'].create({
            'name': 'Test Maintenance',
            'category': 'service',
        })
        cls.contract_type = cls.env['fleet.service.type'].create({
            'name': 'Test Leasing Contract',
            'category': 'contract',
        })

        # Create contract for vehicle 1 within the range
        cls.contract = cls.env['fleet.vehicle.log.contract'].create({
            'vehicle_id': cls.vehicle_1.id,
            'cost_subtype_id': cls.contract_type.id,
            'start_date': cls.past_start,
            'expiration_date': cls.past_end,
            'user_id': cls.env.user.id,
        })

        # Create service log for vehicle 1 within the range
        cls.service = cls.env['fleet.vehicle.log.services'].create({
            'vehicle_id': cls.vehicle_1.id,
            'service_type_id': cls.service_type.id,
            'date_from': cls.past_start + timedelta(days=2),
        })

        # Create odometer reading for vehicle 1 within the range
        cls.odometer = cls.env['fleet.vehicle.odometer'].create({
            'vehicle_id': cls.vehicle_1.id,
            'value': 15000,
            'date': cls.past_start + timedelta(days=5),
        })

        # Create driver assignment history for vehicle 1
        cls.assignation = cls.env['fleet.vehicle.assignation.log'].create({
            'vehicle_id': cls.vehicle_1.id,
            'driver_id': cls.driver.id,
            'date_start': cls.past_start,
            'date_end': cls.past_end,
        })

    def test_01_module_actions_and_views_exist(self):
        """Verify report action, wizard action and view definitions exist."""
        report_action = self.env.ref('fleet_complete_report.action_report_vehicle_detail', raise_if_not_found=False)
        self.assertTrue(report_action, "action_report_vehicle_detail should exist.")
        self.assertEqual(report_action.report_type, 'qweb-pdf')
        self.assertEqual(report_action.model, 'vehicle.detail')

        wizard_action = self.env.ref('fleet_complete_report.vehicle_detail_action', raise_if_not_found=False)
        self.assertTrue(wizard_action, "vehicle_detail_action should exist.")
        self.assertEqual(wizard_action.res_model, 'vehicle.detail')

        form_view = self.env.ref('fleet_complete_report.vehicle_detail_view_form', raise_if_not_found=False)
        self.assertTrue(form_view, "vehicle_detail_view_form should exist.")

    def test_02_wizard_default_values(self):
        """Verify default values upon wizard instantiation."""
        wizard = self.env['vehicle.detail'].create({
            'state_ids': [(6, 0, [self.state_active.id])],
        })
        self.assertEqual(wizard.start_date, self.today)
        self.assertEqual(wizard.end_date, self.today)
        self.assertTrue(wizard.exclude_vehicle_data)

    def test_03_onchange_start_date_adjustments(self):
        """Verify _onchange_start_date behavior when start_date > end_date or in the future."""
        wizard = self.env['vehicle.detail'].new({
            'start_date': self.today + timedelta(days=10),
            'end_date': False,
        })
        wizard._onchange_start_date()
        self.assertEqual(wizard.start_date, self.today, "Future start_date without end_date resets to today.")

        wizard.end_date = self.today - timedelta(days=5)
        wizard.start_date = self.today
        wizard._onchange_start_date()
        self.assertEqual(wizard.start_date, wizard.end_date, "start_date > end_date resets to end_date.")

    def test_04_onchange_end_date_adjustments(self):
        """Verify _onchange_end_date behavior when end_date < start_date or in the future."""
        wizard = self.env['vehicle.detail'].new({
            'start_date': self.today - timedelta(days=10),
            'end_date': self.today - timedelta(days=20),
        })
        wizard._onchange_end_date()
        self.assertEqual(wizard.end_date, wizard.start_date, "end_date < start_date resets to start_date.")

        wizard.end_date = self.today + timedelta(days=15)
        wizard._onchange_end_date()
        self.assertEqual(wizard.end_date, self.today, "Future end_date resets to today.")

    def test_05_onchange_state_ids_filters_vehicles(self):
        """Verify selecting state_ids filters existing vehicle_ids."""
        wizard = self.env['vehicle.detail'].new({
            'state_ids': [(6, 0, [self.state_active.id, self.state_inactive.id])],
            'vehicle_ids': [(6, 0, [self.vehicle_1.id, self.vehicle_2.id])],
        })
        # Narrow state_ids to active state only
        wizard.state_ids = [(6, 0, [self.state_active.id])]
        wizard._onchange_state_ids()
        self.assertEqual(wizard.vehicle_ids.ids, [self.vehicle_1.id])

    def test_06_action_print_report_with_explicit_vehicles(self):
        """Verify action_print_report returns action containing selected vehicle IDs."""
        wizard = self.env['vehicle.detail'].create({
            'state_ids': [(6, 0, [self.state_active.id])],
            'vehicle_ids': [(6, 0, [self.vehicle_1.id])],
            'start_date': self.past_start,
            'end_date': self.past_end,
        })
        action = wizard.action_print_report()
        self.assertTrue(action)
        # Extract report data either directly or from layout configurator context
        report_data = action.get('data') or action.get('context', {}).get('report_action', {}).get('data')
        self.assertIsNotNone(report_data)
        self.assertEqual(report_data.get('vehicle_ids'), [self.vehicle_1.id])

    def test_07_action_print_report_fallback_to_state_ids(self):
        """Verify action_print_report searches by state_ids if vehicle_ids is empty."""
        wizard = self.env['vehicle.detail'].create({
            'state_ids': [(6, 0, [self.state_active.id])],
            'vehicle_ids': [(6, 0, [])],
            'start_date': self.past_start,
            'end_date': self.past_end,
        })
        action = wizard.action_print_report()
        report_data = action.get('data') or action.get('context', {}).get('report_action', {}).get('data')
        self.assertIsNotNone(report_data)
        self.assertIn(self.vehicle_1.id, report_data.get('vehicle_ids'))
        self.assertNotIn(self.vehicle_2.id, report_data.get('vehicle_ids'))

    def test_08_get_report_values_structure_and_records(self):
        """Verify report model returns expected data structure and linked records."""
        wizard = self.env['vehicle.detail'].create({
            'state_ids': [(6, 0, [self.state_active.id])],
            'vehicle_ids': [(6, 0, [self.vehicle_1.id])],
            'start_date': self.past_start,
            'end_date': self.past_end,
            'exclude_vehicle_data': False,
        })
        report_model = self.env['report.fleet_complete_report.report_vehicle_detail']
        vals = report_model.with_context(active_id=wizard.id)._get_report_values(
            wizard.ids, data={'vehicle_ids': [self.vehicle_1.id]},
        )

        expected_keys = [
            'doc_ids', 'docs', 'states', 'state_names', 'vehicles',
            'vehicle_names', 'period', 'contracts', 'services', 'odometers', 'drivers_history',
        ]
        for key in expected_keys:
            self.assertIn(key, vals, f"Key '{key}' must be present in report values.")

        self.assertIn(self.vehicle_1, vals['vehicles'])
        self.assertIn(self.contract, vals['contracts'])
        self.assertIn(self.service, vals['services'])
        self.assertIn(self.odometer, vals['odometers'])
        self.assertIn(self.assignation, vals['drivers_history'])
        self.assertTrue(vals['period'].startswith('From '))

    def test_09_get_report_values_with_none_data(self):
        """Verify report model safely handles None or missing data parameter."""
        wizard = self.env['vehicle.detail'].create({
            'state_ids': [(6, 0, [self.state_active.id])],
            'vehicle_ids': [(6, 0, [self.vehicle_1.id])],
            'start_date': self.past_start,
            'end_date': self.past_end,
        })
        report_model = self.env['report.fleet_complete_report.report_vehicle_detail']
        vals = report_model.with_context(active_id=wizard.id)._get_report_values(
            wizard.ids, data=None,
        )
        self.assertIsNotNone(vals)
        self.assertIn('vehicles', vals)
        self.assertEqual(vals['vehicles'].ids, [self.vehicle_1.id])

    def test_10_render_qweb_pdf_report(self):
        """Verify QWeb PDF report renders successfully for both exclude_vehicle_data modes."""
        report_service = self.env['ir.actions.report']

        # 1. With vehicle details included
        wizard_with_data = self.env['vehicle.detail'].create({
            'state_ids': [(6, 0, [self.state_active.id])],
            'vehicle_ids': [(6, 0, [self.vehicle_1.id])],
            'start_date': self.past_start,
            'end_date': self.past_end,
            'exclude_vehicle_data': False,
        })
        pdf_content, _ = report_service.with_context(active_id=wizard_with_data.id)._render_qweb_pdf(
            'fleet_complete_report.action_report_vehicle_detail',
            [wizard_with_data.id],
            data={'vehicle_ids': [self.vehicle_1.id]},
        )
        self.assertTrue(pdf_content)
        self.assertGreater(len(pdf_content), 0)

        # 2. With vehicle details excluded
        wizard_without_data = self.env['vehicle.detail'].create({
            'state_ids': [(6, 0, [self.state_active.id])],
            'vehicle_ids': [(6, 0, [self.vehicle_1.id])],
            'start_date': self.past_start,
            'end_date': self.past_end,
            'exclude_vehicle_data': True,
        })
        pdf_content_2, _ = report_service.with_context(active_id=wizard_without_data.id)._render_qweb_pdf(
            'fleet_complete_report.action_report_vehicle_detail',
            [wizard_without_data.id],
            data={'vehicle_ids': [self.vehicle_1.id]},
        )
        self.assertTrue(pdf_content_2)
        self.assertGreater(len(pdf_content_2), 0)
