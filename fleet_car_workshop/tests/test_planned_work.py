# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase


class TestPlannedWork(TransactionCase):
    """Test cases for the planned.work model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Product is no longer needed since planned work name is a Char field.

    def setUp(self):
        super().setUp()
        # Create a minimal car.workshop to link planned work to
        self.brand = self.env['fleet.vehicle.model.brand'].create(
            {'name': 'Honda'})
        self.model = self.env['fleet.vehicle.model'].create({
            'name': 'Civic',
            'brand_id': self.brand.id,
        })
        self.fleet_vehicle = self.env['fleet.vehicle'].create(
            {'model_id': self.model.id})
        self.vehicle_detail = self.env['vehicle.details'].create(
            {'vehicle_id': self.fleet_vehicle.id})
        self.stage = self.env['worksheet.stages'].create(
            {'name': 'Planning', 'sequence': 1})
        self.workshop = self.env['car.workshop'].create({
            'name': 'General Service',
            'vehicle_id': self.vehicle_detail.id,
            'stage_id': self.stage.id,
        })

    def test_create_planned_work(self):
        """Test creating a planned work entry."""
        pw = self.env['planned.work'].create({
            'name': 'Oil Change',
            'time_spent': 2.0,
            'work_cost': 150.0,
            'work_id': self.workshop.id,
        })
        self.assertEqual(pw.name, 'Oil Change',
                         "Name should be set correctly.")
        self.assertEqual(pw.time_spent, 2.0,
                         "Estimated time should match.")
        self.assertEqual(pw.work_cost, 150.0,
                         "Work cost should match.")
        self.assertFalse(pw.is_completed,
                         "New planned work should not be completed.")


    def test_planned_work_required_name(self):
        """Test that name is required."""
        self.assertTrue(self.env['planned.work']._fields['name'].required)

    def test_compute_is_invoiced(self):
        """Test the computation of is_invoiced based on invoice_line_ids."""
        pw = self.env['planned.work'].create({
            'name': 'Test Work',
            'work_id': self.workshop.id,
        })
        # Simulate linking an invoice line
        move = self.env['account.move'].create({'move_type': 'out_invoice'})
        line = self.env['account.move.line'].create({
            'move_id': move.id,
            'name': 'Test Work',
            'account_id': self.env['account.journal'].search([('type', '=', 'sale')], limit=1).default_account_id.id
        })
        pw.invoice_line_ids = [(4, line.id)]
        self.assertTrue(pw.is_invoiced)
        
        move.button_cancel()
        self.assertFalse(pw.is_invoiced)


    def test_onchange_is_completed_sets_duration_and_date(self):
        """Test that marking is_completed copies time_spent to duration and sets work_date2."""
        pw = self.env['planned.work'].new({
            'name': 'Oil Change',
            'time_spent': 3.5,
            'is_completed': True,
            'work_id': self.workshop.id,
        })
        pw._onchange_is_completed()
        self.assertEqual(pw.duration, 3.5,
                         "Duration should equal time_spent when completed.")
        self.assertTrue(pw.work_date2,
                        "Completion date (work_date2) should be set.")


    def test_onchange_is_completed_false_no_change(self):
        """Test that _onchange_is_completed does nothing when is_completed is False."""
        pw = self.env['planned.work'].new({
            'name': 'Oil Change',
            'time_spent': 2.0,
            'duration': 0.0,
            'is_completed': False,
            'work_id': self.workshop.id,
        })
        pw._onchange_is_completed()
        self.assertEqual(pw.duration, 0.0,
                         "Duration should not change when not completed.")


    def test_update_planned_work(self):
        """Test updating a planned work entry."""
        pw = self.env['planned.work'].create({
            'name': 'Oil Change',
            'time_spent': 1.0,
            'work_id': self.workshop.id,
        })
        pw.write({'time_spent': 4.0, 'work_cost': 200.0, 'is_completed': True})
        self.assertEqual(pw.time_spent, 4.0)
        self.assertEqual(pw.work_cost, 200.0)
        self.assertTrue(pw.is_completed)


    def test_delete_planned_work(self):
        """Test deleting a planned work entry."""
        pw = self.env['planned.work'].create({
            'name': 'Oil Change',
            'work_id': self.workshop.id,
        })
        pw_id = pw.id
        pw.unlink()
        self.assertFalse(
            self.env['planned.work'].search([('id', '=', pw_id)]),
            "Planned work should be deleted.")

