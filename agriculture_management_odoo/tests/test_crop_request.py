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

class TestCropRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCropRequest, cls).setUpClass()
        cls.company = cls.env.company

        # Create Partner for Farmer
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Farmer',
            'email': 'farmer@example.com',
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
            'location_name': 'Test Farm',
            'location_address': '123 Test Street',
            'location_area': 10.0,
            'location_area_unit': 'acres',
            'location_type': 'plot',
        })

    def test_01_create_crop_request(self):
        """Test the creation of a crop request and default state"""
        crop_request = self.env['crop.request'].create({
            'farmer_id': self.farmer.id,
            'seed_id': self.seed.id,
            'location_id': self.location.id,
            'request_date': '2026-01-01',
        })
        
        # Check initial state and values
        self.assertEqual(crop_request.state, 'draft')
        self.assertEqual(crop_request.farmer_id, self.farmer)
        self.assertEqual(crop_request.seed_id, self.seed)
        self.assertEqual(crop_request.location_id, self.location)
        self.assertNotEqual(crop_request.ref, 'New')

    def test_02_crop_request_state_transitions(self):
        """Test all state transitions for a crop request"""
        crop_request = self.env['crop.request'].create({
            'farmer_id': self.farmer.id,
            'seed_id': self.seed.id,
            'location_id': self.location.id,
            'request_date': '2026-01-01',
        })
        
        # Draft to Confirm
        crop_request.action_confirm()
        self.assertEqual(crop_request.state, 'confirm')

        # Confirm to Ploughing
        crop_request.action_ploughing()
        self.assertEqual(crop_request.state, 'ploughing')

        # Ploughing to Sowing
        crop_request.action_sowing()
        self.assertEqual(crop_request.state, 'sowing')

        # Sowing to Manuring
        crop_request.action_manuring()
        self.assertEqual(crop_request.state, 'manuring')

        # Manuring to Irrigation
        crop_request.action_irrigation()
        self.assertEqual(crop_request.state, 'irrigation')

        # Irrigation to Weeding
        crop_request.action_weeding()
        self.assertEqual(crop_request.state, 'weeding')

        # Weeding to Harvest
        crop_request.action_harvest()
        self.assertEqual(crop_request.state, 'harvest')

        # Harvest to Storage
        crop_request.action_storage()
        self.assertEqual(crop_request.state, 'storage')

        # Storage to Cancel (or draft to cancel)
        crop_request.action_cancel()
        self.assertEqual(crop_request.state, 'cancel')

        # Cancel back to draft
        crop_request.action_draft()
        self.assertEqual(crop_request.state, 'draft')
