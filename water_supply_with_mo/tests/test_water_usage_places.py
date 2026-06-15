# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aleena K (odoo@cybrosys.com)
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
##############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'water_supply_with_mo')
class TestWaterUsagePlaces(TransactionCase):

    def test_create_water_usage_place(self):
        """Test creating a water usage place and validating its fields."""
        place = self.env['water.usage.places'].create({
            'code': 'WUP01',
            'usage_place_name': 'Test Usage Place',
        })
        self.assertEqual(place.code, 'WUP01')
        self.assertEqual(place.usage_place_name, 'Test Usage Place')
        self.assertEqual(place.display_name, 'Test Usage Place')
