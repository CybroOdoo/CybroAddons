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
from odoo import fields
from datetime import timedelta
from odoo.exceptions import UserError

class TestCarWorkshop(TransactionCase):
    """ TestCarWorkshop tests """

    def setUp(self):
        """ Setup method """
        super(TestCarWorkshop, self).setUp()
        
        # Search for an existing partner first to avoid issues with dirty DB schemas
        self.partner = self.env['res.partner'].search([], limit=1)
        if not self.partner:
            partner_vals = {
                'name': 'Test Customer',
            }
            # Handle potential required fields from other modules not in current registry
            if 'group_rfq' in self.env['res.partner']._fields:
                partner_vals['group_rfq'] = 'default'
            if 'group_on' in self.env['res.partner']._fields:
                partner_vals['group_on'] = 'default'
            self.partner = self.env['res.partner'].create(partner_vals)
        
        # Create a fleet vehicle model
        self.vehicle_model = self.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': self.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'}).id,
        })
        
        # Create a fleet vehicle
        self.fleet_vehicle = self.env['fleet.vehicle'].create({
            'model_id': self.vehicle_model.id,
            'license_plate': 'TEST-123',
        })
        
        # Create vehicle details
        self.vehicle_details = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
            'partner_id': self.partner.id,
        })
        
        # Create products for planned work and materials
        self.service_product = self.env['product.product'].create({
            'name': 'Engine Repair',
            'type': 'service',
            'lst_price': 500.0,
        })
        
        self.material_product = self.env['product.product'].create({
            'name': 'Engine Oil',
            'type': 'consu',
            'lst_price': 50.0,
        })
        
        # Create stages
        self.stage_new = self.env['worksheet.stages'].create({
            'name': 'New',
            'sequence': 1,
        })
        self.stage_done = self.env['worksheet.stages'].create({
            'name': 'Done',
            'sequence': 10,
            'is_fold': True,
        })

        # Ensure a sale journal exists for invoice creation tests
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            journal_vals = {
                'name': 'Workshop Journal',
                'type': 'sale',
                'code': 'WSJ',
            }
            if 'nacha_entry_class_code' in self.env['account.journal']._fields:
                journal_vals['nacha_entry_class_code'] = 'PPD'
            self.env['account.journal'].create(journal_vals)

    def test_01_car_workshop_flow(self):
        """ Test the basic flow of car workshop """
        # Create a workshop task
        workshop = self.env['car.workshop'].create({
            'name': 'Test Workshop Task',
            'vehicle_id': self.vehicle_details.id,
            'stage_id': self.stage_new.id,
            'date_assign': fields.Date.today(),
            'date_deadline': fields.Datetime.now() + timedelta(days=1),
        })
        
        workshop._onchange_vehicle_id()
        self.assertEqual(workshop.partner_id, self.partner, "Partner should be correctly linked from vehicle")
        self.assertEqual(workshop.state, 'toinvoice', "Initial state should be waiting")
        
        # Add planned work
        planned_work = self.env['planned.work'].create({
            'work_id': workshop.id,
            'planned_work_id': 'Engine Repair',
            'time_spent': 2.0,
            'work_cost': 500.0,
        })
        self.assertEqual(planned_work.work_cost, 500.0, "Service cost should be 500.0")
        
        # Add materials
        material = self.env['material.used'].create({
            'material_id': workshop.id,
            'material_product_id': self.material_product.id,
            'quantity': 2,
        })
        material._onchange_material_product_id()
        self.assertEqual(material.price, 50.0, "Material price should be copied from product")
        
        # Check total amount calculation
        workshop._compute_amount_total()
        self.assertEqual(workshop.amount_total, 550.0, "Total amount should be 500 (service) + 50 (material price)")
        
        # Test completion of planned work
        planned_work.is_completed = True
        planned_work._onchange_is_completed()
        self.assertEqual(planned_work.duration, 2.0, "Duration should match time_spent when completed")
        
        # Check effective hours
        workshop._compute_effective_hour()
        self.assertEqual(workshop.effective_hour, 2.0, "Effective hours should be 2.0")
        
        # Check remaining hours
        workshop._compute_remaining_hour()
        self.assertEqual(workshop.remaining_hour, 0.0, "Remaining hours should be 0.0")
        
        # Test stage change and write method
        workshop.write({'stage_id': self.stage_done.id})
        self.assertTrue(workshop.date_end, "End date should be set when stage is folded")
        
        # Test invoice creation
        workshop.action_create_invoices()
        self.assertEqual(workshop.state, 'invoiced', "State should change to invoiced")
        self.assertEqual(workshop.invoice_count, 1, "Invoice count should be 1")
        
        # Test action_get_invoices
        action = workshop.action_get_invoices()
        self.assertEqual(action['res_model'], 'account.move')
        


    def test_02_vehicle_details_computes(self):
        """ Test compute methods in vehicle.details """
        self.env['car.workshop'].create({
            'name': 'Test Task for Vehicle',
            'vehicle_id': self.vehicle_details.id,
            'stage_id': self.stage_new.id, # Ensure it has a non-folded stage
        })
        
        # Test _compute_task_count
        self.vehicle_details._compute_task_count()
        self.assertEqual(self.vehicle_details.task_count, 1, "Task count should be 1")
        
        # Test _compute_attached_docs_count
        self.env['ir.attachment'].create({
            'name': 'test.txt',
            'res_model': 'vehicle.details',
            'res_id': self.vehicle_details.id,
            'datas': b'test',
        })
        self.vehicle_details._compute_attached_docs_count()
        self.assertEqual(self.vehicle_details.doc_count, 1, "Doc count should be 1")
        
        # Test attachment_tree_views
        action = self.vehicle_details.attachment_tree_views()
        self.assertEqual(action['res_model'], 'ir.attachment')

    def test_03_scheduler_queue(self):
        """ Test process_demo_scheduler_queue """
        workshop = self.env['car.workshop'].create({
            'name': 'Scheduler Test',
            'vehicle_id': self.vehicle_details.id,
            'date_assign': fields.Date.today() - timedelta(days=1),
            'date_deadline': fields.Datetime.now() + timedelta(days=1),
            'stage_id': self.stage_new.id,
        })
        
        workshop.process_demo_scheduler_queue()
        self.assertTrue(workshop.progress > 0, "Progress should be greater than 0")

    def test_04_errors(self):
        """ Test error cases """
        workshop = self.env['car.workshop'].create({
            'name': 'No Customer Workshop',
            'vehicle_id': self.vehicle_details.id,
        })
        
        # Temporarily remove partner to test error
        self.vehicle_details.partner_id = False
        with self.assertRaises(UserError):
            workshop.action_create_invoices()
            
        self.vehicle_details.partner_id = self.partner
        # Test no planned work error
        with self.assertRaises(UserError):
            workshop.action_create_invoices()

    def test_05_worksheet_stages(self):
        """ Test worksheet stages functions """
        stage = self.env['worksheet.stages'].with_context(default_vehicle_id=self.vehicle_details.id).create({
            'name': 'Context Stage',
        })
        self.assertIn(self.vehicle_details, stage.vehicle_ids, "Vehicle should be in stage vehicle_ids from context")

    def test_06_miscellaneous_functions(self):
        """ Test miscellaneous functions for coverage """

        
        # Test _read_group_stage_ids in car.workshop
        workshop_model = self.env['car.workshop']
        stages = workshop_model._read_group_stage_ids(self.env['worksheet.stages'], [])
        self.assertTrue(len(stages) >= 2) # New and Done created in setup
