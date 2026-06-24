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
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta
from odoo.tools import mute_logger

class TestCarRentalContract(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCarRentalContract, cls).setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@test.com',
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'})
        cls.model = cls.env['fleet.vehicle.model'].create({'name': 'Test Model', 'brand_id': cls.brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({'model_id': cls.model.id, 'license_plate': 'TEST-CONTRACT-001'})
        
        # We need a journal and an account
        cls.journal = cls.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', cls.env.company.id)], limit=1)
        
        cls.account = cls.env['account.account'].create({
            'name': 'Test Account',
            'code': 'TESTACC',
            'account_type': 'asset_receivable',
        })
        
        cls.income_account = cls.env['account.account'].create({
            'name': 'Income Account',
            'code': 'INCACC',
            'account_type': 'income',
        })
        
        # Get or create fleet_service_product
        product_template = cls.env.ref('fleet_rental.fleet_service_product', raise_if_not_found=False)
        if product_template:
            cls.product = cls.env['product.product'].search([('product_tmpl_id', '=', product_template.id)], limit=1)
            cls.product.property_account_income_id = cls.income_account.id
        else:
            cls.product = cls.env['product.product'].create({
                'name': 'Car Rental Service',
                'type': 'service',
                'property_account_income_id': cls.income_account.id,
            })
            cls.env['ir.model.data'].create({
                'name': 'fleet_service_product',
                'module': 'fleet_rental',
                'model': 'product.template',
                'res_id': cls.product.product_tmpl_id.id,
            })

    def test_validate_dates(self):
        """ Test that end date cannot be before start date """
        with self.assertRaises(UserError):
            self.env['car.rental.contract'].create({
                'customer_id': self.customer.id,
                'vehicle_id': self.vehicle.id,
                'cost': 100.0,
                'rent_start_date': date.today(),
                'rent_end_date': date.today() - timedelta(days=1),
                'cost_frequency': 'no',
                'first_payment': 100.0,
            })

    def test_validate_time(self):
        """ Test validate time for rent by hour """
        with self.assertRaises(ValidationError):
            self.env['car.rental.contract'].create({
                'customer_id': self.customer.id,
                'vehicle_id': self.vehicle.id,
                'cost': 100.0,
                'rent_start_date': date.today(),
                'rent_end_date': date.today(),
                'rent_by_hour': True,
                'start_time': '12:00',
                'end_time': '10:00',
                'cost_frequency': 'no',
                'first_payment': 100.0,
            })

    def test_action_run(self):
        """ Test action run changes state """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
        })
        contract.action_run()
        self.assertEqual(contract.state, 'running')
        # Check that state_changer worked
        self.assertEqual(contract.vehicle_id.state_id.id, self.env.ref('fleet_rental.vehicle_state_rent').id)

    def test_action_cancel(self):
        """ Test action cancel changes state """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
        })
        contract.action_cancel()
        self.assertEqual(contract.state, 'cancel')
        self.assertTrue(contract.vehicle_id.rental_check_availability)
        self.assertEqual(contract.vehicle_id.state_id.id, self.env.ref('fleet_rental.vehicle_state_active').id)

    def test_action_confirm(self):
        """ Test action confirm """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
        })
        contract.action_confirm()
        self.assertEqual(contract.state, 'reserved')
        self.assertFalse(contract.vehicle_id.rental_check_availability)
        self.assertTrue(contract.reserved_fleet_id)

    def test_extend_rent(self):
        """ Test extend rent operations """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
        })
        contract.action_confirm()
        
        contract.action_extend_rent()
        self.assertTrue(contract.read_only)
        
        contract.rent_end_date = date.today() + timedelta(days=5)
        contract.action_confirm_extend_rent()
        self.assertFalse(contract.read_only)
        self.assertEqual(contract.vehicle_id.rental_reserved_time.date_to, date.today() + timedelta(days=5))

    def test_action_invoice_create(self):
        """ Test invoice creation """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
        })
        result = contract.action_invoice_create()
        self.assertTrue(contract.first_invoice_created)
        self.assertTrue(contract.first_payment_inv)
        self.assertEqual(result['res_model'], 'account.move')
