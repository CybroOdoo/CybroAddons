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


class TestVehicleDetails(TransactionCase):
    """Test cases for the vehicle.details model."""

    def setUp(self):
        super().setUp()
        self.brand = self.env['fleet.vehicle.model.brand'].create(
            {'name': 'Toyota'})
        self.model = self.env['fleet.vehicle.model'].create({
            'name': 'Corolla',
            'brand_id': self.brand.id,
        })
        self.fleet_vehicle = self.env['fleet.vehicle'].create({
            'model_id': self.model.id,
        })
        self.partner = self.env['res.partner'].create({'name': 'John Doe'})

    def test_create_vehicle_details(self):
        """Test creating a vehicle details record."""
        vehicle = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
            'partner_id': self.partner.id,
            'state': 'open',
        })
        self.assertEqual(vehicle.vehicle_id.id, self.fleet_vehicle.id,
                         "Fleet vehicle should be linked correctly.")
        self.assertEqual(vehicle.partner_id.id, self.partner.id,
                         "Partner should be linked correctly.")
        self.assertEqual(vehicle.state, 'open',
                         "Default state should be 'open'.")


    def test_vehicle_required_field(self):
        """Test that vehicle_id is required."""
        self.assertTrue(self.env['vehicle.details']._fields['vehicle_id'].required)


    def test_vehicle_state_transitions(self):
        """Test the valid state transitions for a vehicle detail record."""
        vehicle = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
            'state': 'draft',
        })
        self.assertEqual(vehicle.state, 'draft')
        vehicle.write({'state': 'open'})
        self.assertEqual(vehicle.state, 'open')
        vehicle.write({'state': 'pending'})
        self.assertEqual(vehicle.state, 'pending')
        vehicle.write({'state': 'close'})
        self.assertEqual(vehicle.state, 'close')
        vehicle.write({'state': 'cancelled'})
        self.assertEqual(vehicle.state, 'cancelled')


    def test_task_count_computation(self):
        """Test that _compute_task_count returns the correct count."""
        vehicle = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
        })
        self.assertEqual(vehicle.task_count, 0,
                         "New vehicle should have 0 tasks.")
        stage = self.env['worksheet.stages'].create(
            {'name': 'New', 'sequence': 1})
        self.env['car.workshop'].create({
            'name': 'Test Worksheet',
            'vehicle_id': vehicle.id,
            'stage_id': stage.id,
        })
        vehicle.invalidate_recordset()
        self.assertEqual(vehicle.task_count, 1,
                         "Vehicle task count should be 1 after creating a worksheet.")


    def test_active_field_and_archive(self):
        """Test archiving (deactivating) a vehicle detail record and the compute/inverse archive field."""
        vehicle = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
            'active': True,
        })
        self.assertTrue(vehicle.active)
        self.assertFalse(vehicle.archive, "Archive should be False when active is True")
        
        # Test inverse
        vehicle.write({'archive': True})
        self.assertTrue(vehicle.archive)
        self.assertFalse(vehicle.active, "Active should be False when archive is True")
        
        # Test compute
        vehicle.write({'active': True})
        self.assertTrue(vehicle.active)
        self.assertFalse(vehicle.archive, "Archive should be computed back to False when active is True")

    def test_get_visibility_selection_id(self):
        """Test the _get_visibility_selection_id method."""
        vehicle = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
        })
        selection = vehicle._get_visibility_selection_id()
        self.assertTrue(isinstance(selection, list), "Selection should be a list")
    def test_attached_docs_count(self):
        """Test that _compute_attached_docs_count returns 0 for a new record."""
        vehicle = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
        })
        self.assertEqual(vehicle.doc_count, 0,
                         "New vehicle should have 0 attached documents.")


    def test_attachment_tree_view_action(self):
        """Test that attachment_tree_views returns a valid action dict."""
        vehicle = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
        })
        action = vehicle.attachment_tree_views()
        self.assertEqual(action['type'], 'ir.actions.act_window',
                         "Action type should be act_window.")
        self.assertEqual(action['res_model'], 'ir.attachment',
                         "Action res_model should be ir.attachment.")


    def test_update_vehicle_details(self):
        """Test updating vehicle detail fields."""
        vehicle = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
            'state': 'draft',
        })
        vehicle.write({'state': 'close', 'partner_id': self.partner.id})
        self.assertEqual(vehicle.state, 'close')
        self.assertEqual(vehicle.partner_id.id, self.partner.id)


    def test_delete_vehicle_details(self):
        """Test deleting a vehicle details record."""
        vehicle = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
        })
        vehicle_id = vehicle.id
        vehicle.unlink()
        self.assertFalse(
            self.env['vehicle.details'].search([('id', '=', vehicle_id)]),
            "Vehicle details record should be deleted.")

