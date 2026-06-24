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

class TestFleetRentalLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestFleetRentalLine, cls).setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
        
        # Need a car rental contract, but it requires a lot of fields, we can mock or just create a minimal one.
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'})
        cls.model = cls.env['fleet.vehicle.model'].create({'name': 'Test Model', 'brand_id': cls.brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({'model_id': cls.model.id, 'license_plate': 'TEST-LINE-001'})
        
        cls.contract = cls.env['car.rental.contract'].create({
            'customer_id': cls.customer.id,
            'vehicle_id': cls.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today(),
            'cost_frequency': 'no',
            'first_payment': 100.0,
        }) if 'car.rental.contract' in cls.env else False
        
        # We need an account move to test the payment info
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.customer.id,
        })

    def test_paid_info(self):
        """ Test paid info """
        line = self.env['fleet.rental.line'].create({
            'name': 'Test Line',
            'recurring_amount': 50.0,
            'invoice_number': self.invoice.id,
            'invoice_ref': self.invoice.id,
        })
        if self.contract:
            line.rental_number = self.contract.id
            
        line.paid_info()
        self.assertEqual(line.payment_info, 'draft')
        
