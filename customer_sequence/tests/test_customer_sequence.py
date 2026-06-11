# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gee Paul Joby (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase

class TestCustomerSequence(TransactionCase):

    def setUp(self):
        super(TestCustomerSequence, self).setUp()
        self.company = self.env.user.company_id
        # Reset company next_code and set customer_code
        self.company.write({
            'customer_code': 1000,
            'next_code': 0,
        })
        self.Partner = self.env['res.partner']

    def test_01_customer_sequence_initial(self):
        """Test sequence generation when next_code is not set initially."""
        partner = self.Partner.create({
            'name': 'Test Customer 1',
            'customer_rank': 1,
        })
        
        self.assertEqual(partner.unique_id, '1000', "Unique ID should be 1000")
        self.assertEqual(partner.name, '[1000]Test Customer 1', "Name should be prefixed with code")
        self.assertEqual(self.company.next_code, 1001, "Next code should be incremented to 1001")

    def test_02_customer_sequence_next_code(self):
        """Test sequence generation when next_code is set."""
        self.company.write({'next_code': 2000})
        partner = self.Partner.create({
            'name': 'Test Customer 2',
            'customer_rank': 1,
        })
        
        self.assertEqual(partner.unique_id, '2000', "Unique ID should be 2000")
        self.assertEqual(partner.name, '[2000]Test Customer 2', "Name should be prefixed with code")
        self.assertEqual(self.company.next_code, 2001, "Next code should be incremented to 2001")

    def test_03_non_customer_sequence(self):
        """Test that sequence is not generated for non-customers."""
        partner = self.Partner.create({
            'name': 'Test Vendor',
            'customer_rank': 0,
            'supplier_rank': 1,
        })
        
        self.assertEqual(partner.unique_id, '/', "Unique ID should be '/' for non-customers")
        self.assertEqual(partner.name, 'Test Vendor', "Name should remain unchanged")

    def test_04_customer_sequence_multi(self):
        """Test sequence generation when multiple partners are created at once."""
        partners = self.Partner.create([
            {'name': 'Test Multi 1', 'customer_rank': 1},
            {'name': 'Test Multi 2', 'customer_rank': 1},
        ])
        
        self.assertEqual(len(partners), 2)
        self.assertEqual(partners[0].unique_id, '1000')
        self.assertEqual(partners[1].unique_id, '1001')
        self.assertEqual(self.company.next_code, 1002)
