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

class TestVenueLines(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.amenity = cls.env['amenities'].create({'name': 'Speaker', 'amount': 15.0})
        cls.venue_type = cls.env['venue.type'].create({'name': 'Auditorium'})
        cls.venue = cls.env['venue'].create({
            'name': 'Grand Auditorium',
            'venue_type_id': cls.venue_type.id,
            'venue_location': 'West Wing',
            'capacity': 200,
            'seating': 200,
            'venue_charge_hour': 200.0,
            'venue_charge_day': 2000.0,
        })
        cls.venue_line = cls.env['venue.lines'].create({
            'venue_id': cls.venue.id,
            'amenities_id': cls.amenity.id,
            'quantity': 4,
        })

    def test_venue_line_sub_total(self):
        """Test sub total computation for venue lines."""
        self.assertEqual(self.venue_line.sub_total, 60.0)
