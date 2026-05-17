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

class TestPropertyAreaMeasure(TransactionCase):

    def setUp(self):
        super(TestPropertyAreaMeasure, self).setUp()
        self.area_measure = self.env['property.area.measure'].create({
            'name': 'Test Section',
            'length': 10,
            'width': 20,
        })

    def test_compute_area(self):
        """Test calculation of area"""
        self.area_measure._compute_area()
        self.assertEqual(self.area_measure.area, 200)
