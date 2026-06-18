# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Arjun P P (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests import common
from odoo import fields


class TestVehicleDetail(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create Brand and Model
        cls.brand = cls.env["fleet.vehicle.model.brand"].create({"name": "Tesla"})
        cls.model = cls.env["fleet.vehicle.model"].create({
            "brand_id": cls.brand.id,
            "name": "Model 3",
        })

        # Create States
        cls.state_active = cls.env["fleet.vehicle.state"].create({"name": "Active", "sequence": 1})
        cls.state_inactive = cls.env["fleet.vehicle.state"].create({"name": "Inactive", "sequence": 2})

        # Create Vehicles
        cls.vehicle_1 = cls.env["fleet.vehicle"].create({
            "model_id": cls.model.id,
            "license_plate": "EL-123-AA",
            "state_id": cls.state_active.id,
            "plan_to_change_car": False,
        })
        cls.vehicle_2 = cls.env["fleet.vehicle"].create({
            "model_id": cls.model.id,
            "license_plate": "EL-456-BB",
            "state_id": cls.state_inactive.id,
            "plan_to_change_car": False,
        })

    def test_01_default_values(self):
        """Test default values of vehicle.detail transient model."""
        wizard = self.env['vehicle.detail'].create({
            'state_ids': [(6, 0, [self.state_active.id])],
        })
        self.assertEqual(wizard.start_date, fields.Date.today())
        self.assertEqual(wizard.end_date, fields.Date.today())
        self.assertTrue(wizard.exclude_vehicle_data)

    def test_02_onchanges(self):
        """Test the onchanges for start_date, end_date, and state_ids."""
        today = fields.Date.today()
        yesterday = fields.Date.add(today, days=-1)
        tomorrow = fields.Date.add(today, days=1)

        # 1. Onchange start_date (end_date not set, start_date in future)
        wizard = self.env['vehicle.detail'].new({
            'start_date': tomorrow,
            'end_date': False,
        })
        wizard._onchange_start_date()
        self.assertEqual(wizard.start_date, today)

        # 2. Onchange start_date (start_date after end_date)
        wizard = self.env['vehicle.detail'].new({
            'start_date': today,
            'end_date': yesterday,
        })
        wizard._onchange_start_date()
        self.assertEqual(wizard.start_date, yesterday)

        # 3. Onchange end_date (start_date after end_date)
        wizard = self.env['vehicle.detail'].new({
            'start_date': today,
            'end_date': yesterday,
        })
        wizard._onchange_end_date()
        self.assertEqual(wizard.end_date, today)

        # 4. Onchange end_date (end_date in future)
        wizard = self.env['vehicle.detail'].new({
            'start_date': yesterday,
            'end_date': tomorrow,
        })
        wizard._onchange_end_date()
        self.assertEqual(wizard.end_date, today)

        # 5. Onchange state_ids filters vehicle_ids (using new and checking ids)
        wizard = self.env['vehicle.detail'].new({
            'state_ids': [(6, 0, [self.state_active.id])],
            'vehicle_ids': [(6, 0, [self.vehicle_1.id, self.vehicle_2.id])],
        })
        wizard._onchange_state_ids()
        self.assertEqual(wizard.vehicle_ids.ids, [self.vehicle_1.id])

    def test_03_action_print_report(self):
        """Test action_print_report behavior with different selections."""
        # Case 1: Specific vehicles chosen
        wizard = self.env['vehicle.detail'].create({
            'state_ids': [(6, 0, [self.state_active.id])],
            'vehicle_ids': [(6, 0, [self.vehicle_1.id])],
        })
        # Use discard_logo_check to bypass base layout configurator redirection
        action = wizard.with_context(discard_logo_check=True).action_print_report()
        self.assertEqual(action['report_name'], 'fleet_complete_report.report_vehicle_detail')
        self.assertEqual(action['context']['active_ids'], wizard.ids)

        # Case 2: No specific vehicles, but states selected
        wizard_state = self.env['vehicle.detail'].create({
            'state_ids': [(6, 0, [self.state_inactive.id])],
        })
        action_state = wizard_state.with_context(discard_logo_check=True).action_print_report()
        self.assertEqual(action_state['data']['vehicle_ids'], [self.vehicle_2.id])

        # Case 3: Neither vehicles nor states selected (search all)
        wizard_all = self.env['vehicle.detail'].create({
            'state_ids': [(6, 0, [self.state_active.id, self.state_inactive.id])],
        })
        # Reset state_ids to empty (we bypass require=True check in Python code)
        wizard_all.write({'state_ids': [(5, 0, 0)]})
        action_all = wizard_all.with_context(discard_logo_check=True).action_print_report()
        self.assertIn(self.vehicle_1.id, action_all['data']['vehicle_ids'])
        self.assertIn(self.vehicle_2.id, action_all['data']['vehicle_ids'])

    def test_04_report_values(self):
        """Test the values returned by _get_report_values of ReportVehicleDetail."""
        today = fields.Date.today()
        yesterday = fields.Date.add(today, days=-1)

        # Create Logs
        contract = self.env['fleet.vehicle.log.contract'].create({
            'vehicle_id': self.vehicle_1.id,
            'start_date': yesterday,
            'expiration_date': today,
        })
        # Note: fleet.vehicle.log.services might require service_type_id or other fields in Odoo 19
        service_type = self.env['fleet.service.type'].create({
            'name': 'Oil Change',
            'category': 'service',
        })
        service = self.env['fleet.vehicle.log.services'].create({
            'vehicle_id': self.vehicle_1.id,
            'date': today,
            'description': 'Test Service',
            'service_type_id': service_type.id,
        })
        odometer = self.env['fleet.vehicle.odometer'].create({
            'vehicle_id': self.vehicle_1.id,
            'date': today,
            'value': 10000,
        })
        driver_history = self.env['fleet.vehicle.assignation.log'].create({
            'vehicle_id': self.vehicle_1.id,
            'driver_id': self.env.user.partner_id.id,
            'date_start': yesterday,
            'date_end': today,
        })

        wizard = self.env['vehicle.detail'].create({
            'state_ids': [(6, 0, [self.state_active.id, self.state_inactive.id])],
            'vehicle_ids': [(6, 0, [self.vehicle_1.id, self.vehicle_2.id])],
            'start_date': yesterday,
            'end_date': today,
        })

        report_model = self.env['report.fleet_complete_report.report_vehicle_detail']
        # Call with active_id context and en_US lang
        context = {
            'active_id': wizard.id,
            'lang': 'en_US',
        }
        res = report_model.with_context(context)._get_report_values(
            docids=[wizard.id],
            data={'vehicle_ids': [self.vehicle_1.id, self.vehicle_2.id]}
        )

        self.assertEqual(res['docs'], wizard)
        self.assertIn(self.state_active, res['states'])
        self.assertIn(self.vehicle_1, res['vehicles'])
        self.assertIn(contract, res['contracts'])
        self.assertIn(service, res['services'])
        self.assertIn(odometer, res['odometers'])
        self.assertIn(driver_history, res['drivers_history'])
