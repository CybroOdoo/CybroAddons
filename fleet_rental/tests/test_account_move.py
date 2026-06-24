# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
from datetime import date

class TestAccountMove(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountMove, cls).setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
        
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'})
        cls.model = cls.env['fleet.vehicle.model'].create({'name': 'Test Model', 'brand_id': cls.brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({'model_id': cls.model.id, 'license_plate': 'TEST-INV-001'})
        
        # create a car.rental.contract for the fleet_rent_id
        cls.contract = cls.env['car.rental.contract'].create({
            'customer_id': cls.customer.id,
            'vehicle_id': cls.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today(),
            'cost_frequency': 'no',
            'first_payment': 100.0,
            'state': 'running',
        })
        
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.customer.id,
            'fleet_rent_id': cls.contract.id,
        })

    def test_button_cancel(self):
        """ Test button cancel for invoice linked to rental contract """
        # When contract state is 'running'
        self.invoice.button_cancel()
        self.assertEqual(self.contract.state, 'running')
        self.assertFalse(self.contract.first_invoice_created)
        
        # When contract state is not 'running'
        self.contract.state = 'done'
        self.invoice.button_draft()
        self.invoice.button_cancel()
        self.assertEqual(self.contract.state, 'checking')
