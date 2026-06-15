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
class TestWaterUsageCategories(TransactionCase):

    def test_create_water_usage_category(self):
        """Test creating a water usage category and validating its fields."""
        category = self.env['water.usage.categories'].create({
            'code': 'WUC01',
            'usage_category_name': 'Test Usage Category',
        })
        self.assertEqual(category.code, 'WUC01')
        self.assertEqual(category.usage_category_name, 'Test Usage Category')
        self.assertEqual(category.display_name, 'Test Usage Category')
