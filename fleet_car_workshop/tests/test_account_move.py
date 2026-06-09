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

class TestAccountMove(TransactionCase):
    """ TestAccountMove tests """

    def setUp(self):
        """ Setup method """
        super(TestAccountMove, self).setUp()
        
        # Setup similar to test_car_workshop
        self.partner = self.env['res.partner'].search([], limit=1)
        if not self.partner:
            self.partner = self.env['res.partner'].create({'name': 'Test Customer'})
            
        self.vehicle_model = self.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': self.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'}).id,
        })
        
        self.fleet_vehicle = self.env['fleet.vehicle'].create({
            'model_id': self.vehicle_model.id,
            'license_plate': 'TEST-123',
        })
        
        self.vehicle_details = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
            'partner_id': self.partner.id,
        })
        
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
        
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            self.env['account.journal'].create({
                'name': 'Workshop Journal',
                'type': 'sale',
                'code': 'WSJ',
            })
            
        self.workshop = self.env['car.workshop'].create({
            'name': 'Test Invoice Cancel Delete',
            'vehicle_id': self.vehicle_details.id,
            'date_assign': fields.Date.today(),
            'date_deadline': fields.Datetime.now() + timedelta(days=1),
        })
        
        self.workshop._onchange_vehicle_id()
        
        self.planned_work = self.env['planned.work'].create({
            'work_id': self.workshop.id,
            'planned_work_id': 'Engine Repair',
            'time_spent': 2.0,
            'work_cost': 500.0,
            'is_completed': True,
        })
        
        self.material = self.env['material.used'].create({
            'material_id': self.workshop.id,
            'material_product_id': self.material_product.id,
            'quantity': 2,
        })
        self.material._onchange_material_product_id()

    def test_cancel_invoice(self):
        """ Test that cancelling an invoice resets the is_invoiced flag """
        self.workshop.action_create_invoices()
        self.assertTrue(self.planned_work.is_invoiced)
        self.assertTrue(self.material.is_invoiced)
        
        # Get the created invoice
        invoice = self.env['account.move'].search([('invoice_origin', '=', self.workshop.name)], limit=1)
        self.assertTrue(invoice)
        
        # Cancel the invoice
        invoice.button_cancel()
        
        # Check if flags are reset
        self.assertFalse(self.planned_work.is_invoiced)
        self.assertFalse(self.material.is_invoiced)
        self.assertEqual(self.workshop.state, 'toinvoice')

    def test_unlink_invoice(self):
        """ Test that deleting an invoice resets the is_invoiced flag """
        self.workshop.action_create_invoices()
        self.assertTrue(self.planned_work.is_invoiced)
        self.assertTrue(self.material.is_invoiced)
        
        # Get the created invoice
        invoice = self.env['account.move'].search([('invoice_origin', '=', self.workshop.name)], limit=1)
        
        # Delete the invoice (set it to draft first if needed, though button_cancel already does this usually)
        invoice.button_cancel()
        invoice.unlink()
        
        # Check if flags are reset
        self.assertFalse(self.planned_work.is_invoiced)
        self.assertFalse(self.material.is_invoiced)
        self.assertEqual(self.workshop.state, 'toinvoice')
