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

class TestPropertyProperty(TransactionCase):

    def setUp(self):
        super(TestPropertyProperty, self).setUp()
        self.country = self.env.ref('base.in')
        self.property = self.env['property.property'].create({
            'name': 'Test Property',
            'property_type': 'residential',
            'street': 'Test Street',
            'country_id': self.country.id,
            'sale_rent': 'for_sale',
        })

    def test_property_creation(self):
        """Test sequence generation on creation"""
        self.assertNotEqual(self.property.code, 'New')
        self.assertTrue(self.property.code.startswith('PI/'))

    def test_compute_total_sq_feet(self):
        """Test calculation of total square feet"""
        self.env['property.area.measure'].create({
            'name': 'Living Room',
            'length': 50,
            'width': 10,
            'property_id': self.property.id,
        })
        self.env['property.area.measure'].create({
            'name': 'Bedroom',
            'length': 30,
            'width': 10,
            'property_id': self.property.id,
        })
        self.property._compute_total_sq_feet()
        self.assertEqual(self.property.total_sq_feet, 800)

    def test_action_available(self):
        """Test action_available state transition"""
        self.property.state = 'draft'
        self.property.action_available()
        self.assertEqual(self.property.state, 'available')

    def test_action_property_sale_view(self):
        """Test action_property_sale_view return value"""
        action = self.property.action_property_sale_view()
        self.assertEqual(action['res_model'], 'property.sale')
        self.assertEqual(action['view_mode'], 'list,form')

    def test_action_property_rental_view(self):
        """Test action_property_rental_view return value"""
        action = self.property.action_property_rental_view()
        self.assertEqual(action['res_model'], 'property.rental')
        self.assertEqual(action['view_mode'], 'list,form')
