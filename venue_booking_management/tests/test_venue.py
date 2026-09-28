# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase
from odoo import Command

class TestVenue(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.venue_type = cls.env['venue.type'].create({'name': 'Hall'})
        cls.amenity = cls.env['amenities'].create({'name': 'Mic', 'amount': 20.0})
        cls.venue = cls.env['venue'].create({
            'name': 'Main Hall',
            'venue_type_id': cls.venue_type.id,
            'venue_location': 'City Center',
            'capacity': 50,
            'seating': 50,
            'venue_charge_hour': 100.0,
            'venue_charge_day': 1000.0,
            'additional_charge_hour': 10.0,
            'additional_charge_day': 100.0,
            'venue_line_ids': [
                Command.create({
                    'amenities_id': cls.amenity.id,
                    'quantity': 2,
                })
            ]
        })

    def test_venue_creation_and_computes(self):
        """Test venue price subtotal computation and creation."""
        self.assertEqual(self.venue.name, 'Main Hall')
        self.assertEqual(self.venue.price_subtotal, 40.0)
