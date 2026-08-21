# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import timedelta, date

class TestPestRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestPestRequest, cls).setUpClass()
        cls.company = cls.env.company

        # Create Partner for Farmer
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Farmer Pest',
            'email': 'farmer_pest@example.com',
        })

        # Create Farmer Detail
        cls.farmer = cls.env['farmer.detail'].create({
            'farmer_id': cls.partner.id,
            'note': 'Test note for farmer',
        })

        # Create Seed Detail
        cls.seed = cls.env['seed.detail'].create({
            'name': 'Test Wheat',
            'quantity': 100,
            'unit': 'kg',
            'seed_type': 'certified',
        })

        # Create Location Detail
        cls.location = cls.env['location.detail'].create({
            'location_name': 'Test Farm Pest',
            'location_address': '123 Test Street',
            'location_area': 10.0,
            'location_area_unit': 'acres',
            'location_type': 'plot',
        })

        # Create Crop Request
        cls.crop = self.env['crop.request'] if hasattr(self, 'env') else cls.env['crop.request'].create({
            'farmer_id': cls.farmer.id,
            'seed_id': cls.seed.id,
            'location_id': cls.location.id,
            'request_date': date.today(),
        })

        # Create Pest Detail (Valid)
        cls.pest_valid = cls.env['pest.detail'].create({
            'pest_name': 'Valid Pest',
            'pest_expiry_date': date.today() + timedelta(days=10),
            'pest_cost': 50.0,
            'pest_quantity': 100,
        })
        
        # Create Pest Detail (Expired)
        cls.pest_expired = cls.env['pest.detail'].create({
            'pest_name': 'Expired Pest',
            'pest_expiry_date': date.today() - timedelta(days=10),
            'pest_cost': 20.0,
            'pest_quantity': 50,
        })

    def test_01_pest_request_creation(self):
        """Test pest request creation and computations"""
        pest_req = self.env['pest.request'].create({
            'farmer_id': self.farmer.id,
            'crop_id': self.crop.id,
            'pest_id': self.pest_valid.id,
            'pest_quantity': 5,
            'disease': 'Test Disease',
        })
        
        self.assertEqual(pest_req.state, 'draft')
        self.assertEqual(pest_req.total_cost, 250.0)  # 50.0 * 5
        self.assertNotEqual(pest_req.reference, 'New')

    def test_02_pest_request_states(self):
        """Test pest request state transitions with valid pest"""
        pest_req = self.env['pest.request'].create({
            'farmer_id': self.farmer.id,
            'crop_id': self.crop.id,
            'pest_id': self.pest_valid.id,
            'pest_quantity': 5,
            'disease': 'Test Disease',
        })
        
        pest_req.action_pending()
        self.assertEqual(pest_req.state, 'pending')

        pest_req.action_approved()
        self.assertEqual(pest_req.state, 'approve')

        pest_req.action_rejected()
        self.assertEqual(pest_req.state, 'rejected')
        
        pest_req.action_draft()
        self.assertEqual(pest_req.state, 'draft')

    def test_03_pest_request_expired_validation(self):
        """Test validation when using expired pest"""
        pest_req = self.env['pest.request'].create({
            'farmer_id': self.farmer.id,
            'crop_id': self.crop.id,
            'pest_id': self.pest_expired.id,
            'pest_quantity': 5,
            'disease': 'Test Disease',
        })
        
        with self.assertRaises(ValidationError):
            pest_req.action_pending()
            
        with self.assertRaises(ValidationError):
            pest_req.action_approved()
