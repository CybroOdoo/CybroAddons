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
from odoo.tests import TransactionCase

class TestVehicleDetails(TransactionCase):
    """ TestVehicleDetails tests """

    def setUp(self):
        """ Setup method """
        super(TestVehicleDetails, self).setUp()
        self.vehicle_model = self.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': self.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'}).id,
        })
        self.fleet_vehicle = self.env['fleet.vehicle'].create({
            'model_id': self.vehicle_model.id,
            'license_plate': 'TEST-DET',
        })
        self.vehicle_details = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
        })

    def test_compute_task_count(self):
        """ Test _compute_task_count function """
        stage = self.env['worksheet.stages'].create({
            'name': 'Active Stage',
            'is_fold': False,
        })
        self.env['car.workshop'].create({
            'name': 'Task 1',
            'vehicle_id': self.vehicle_details.id,
            'stage_id': stage.id,
        })
        self.vehicle_details._compute_task_count()
        self.assertEqual(self.vehicle_details.task_count, 1)

    def test_compute_attached_docs_count(self):
        """ Test _compute_attached_docs_count function """
        self.env['ir.attachment'].create({
            'name': 'Doc 1',
            'res_model': 'vehicle.details',
            'res_id': self.vehicle_details.id,
            'datas': b'test',
        })
        self.vehicle_details._compute_attached_docs_count()
        self.assertEqual(self.vehicle_details.doc_count, 1)

    def test_attachment_tree_views(self):
        """ Test attachment_tree_views function """
        action = self.vehicle_details.attachment_tree_views()
        self.assertEqual(action['res_model'], 'ir.attachment')
        self.assertEqual(action['type'], 'ir.actions.act_window')

    def test_create_write_is_archive(self):
        """ Test create and write methods for is_archive toggling """
        # Test create with is_archive=True
        archived_vehicle = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
            'is_archive': True,
        })
        self.assertFalse(archived_vehicle.active, "Vehicle should be inactive if created with is_archive=True")

        # Test write to toggle is_archive
        self.assertTrue(self.vehicle_details.active)
        self.vehicle_details.write({'is_archive': True})
        self.assertFalse(self.vehicle_details.active, "Vehicle should be inactive after setting is_archive=True")

        self.vehicle_details.write({'is_archive': False})
        self.assertTrue(self.vehicle_details.active, "Vehicle should be active after setting is_archive=False")
