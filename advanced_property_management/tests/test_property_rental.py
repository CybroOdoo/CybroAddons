# -*- coding: utf-8 -*-
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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError
from odoo import fields

class TestPropertyRental(TransactionCase):

    def setUp(self):
        super(TestPropertyRental, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Renter'})
        self.property = self.env['property.property'].create({
            'name': 'Test Rental Property',
            'property_type': 'residential',
            'street': 'Test Street',
            'country_id': self.env.ref('base.in').id,
            'sale_rent': 'for_tenancy',
            'rent_month': 1000,
            'state': 'available',
        })
        self.account = self.env['account.account'].create({
            'name': 'Income Account',
            'code': 'INC001',
            'account_type': 'income',
            'company_ids': [fields.Command.set(self.env.company.ids)],
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Sales Journal',
            'code': 'SALE',
            'type': 'sale',
            'company_id': self.env.company.id,
        })
        self.rental = self.env['property.rental'].create({
            'property_id': self.property.id,
            'renter_id': self.partner.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.add(fields.Date.today(), months=6),
            'rent_price': 1000,
        })

    def test_rental_creation(self):
        """Test sequence generation on creation"""
        self.assertNotEqual(self.rental.name, 'New')

    def test_compute_invoice_count(self):
        """Test calculation of invoice count"""
        self.rental._compute_invoice_count()
        self.assertEqual(self.rental.invoice_count, 0)
        # Create a dummy invoice
        self.env['account.move'].create({
            'move_type': 'out_invoice',
            'property_rental_id': self.rental.id,
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
        })
        self.rental._compute_invoice_count()
        self.assertEqual(self.rental.invoice_count, 1)

    def test_compute_next_invoice(self):
        """Test calculation of next invoice date"""
        self.rental.invoice_date = fields.Date.today()
        self.rental._compute_next_invoice()
        expected_date = fields.Date.add(fields.Date.today(), months=1)
        self.assertEqual(self.rental.next_invoice, expected_date)

    def test_action_cancel(self):
        """Test action_cancel logic"""
        self.rental.action_cancel()
        self.assertEqual(self.rental.state, 'cancel')
        self.assertEqual(self.property.state, 'available')

    def test_action_create_contract(self):
        """Test contract creation and blacklisted check"""
        # Test success
        self.rental.action_create_contract()
        self.assertEqual(self.rental.state, 'in_contract')
        self.assertEqual(self.property.state, 'rented')
        self.assertTrue(self.rental.invoice_date)

        # Test blacklisted
        self.partner.blacklisted = True
        rental2 = self.env['property.rental'].create({
            'property_id': self.property.id,
            'renter_id': self.partner.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.add(fields.Date.today(), months=6),
        })
        with self.assertRaises(ValidationError):
            rental2.action_create_contract()

    def test_setup_account_findable(self):
        """Debug test to check if account is findable"""
        acc = self.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', self.env.company.id)
        ], limit=1)
        self.assertTrue(acc, f"Income account should be findable in company {self.env.company.id}")

    def test_action_check_rental(self):
        """Test scheduled action action_check_rental"""
        self.rental.state = 'in_contract'
        self.rental.invoice_date = fields.Date.today()
        self.rental._compute_next_invoice()
        
        # Mock next invoice to be today to trigger invoice creation
        self.rental.next_invoice = fields.Date.today()
        self.env['property.rental'].action_check_rental()
        
        # Check if a new invoice was created (originally 0, now should be 1)
        # Note: action_create_contract was not called, so we check total invoices
        invoice_count = self.env['account.move'].search_count([('property_rental_id', '=', self.rental.id)])
        self.assertEqual(invoice_count, 1)
