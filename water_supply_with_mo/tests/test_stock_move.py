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
class TestStockMove(TransactionCase):

    def test_stock_move_relation(self):
        """Test that stock.move correctly relates to water.supply.request."""
        product = self.env['product.product'].create({
            'name': 'Test Water Product',
            'type': 'consu',
        })
        place = self.env['water.usage.places'].create({
            'code': 'UP1',
            'usage_place_name': 'Place 1',
        })
        category = self.env['water.usage.categories'].create({
            'code': 'UC1',
            'usage_category_name': 'Category 1',
        })
        method = self.env['water.supply.methods'].create({
            'code': 'M1',
            'supply_name': 'Method 1',
        })
        partner = self.env['res.partner'].create({
            'name': 'Test Customer',
        })
        request = self.env['water.supply.request'].create({
            'partner_id': partner.id,
            'pickup_date': '2026-06-20',
            'usage_place_id': place.id,
            'usage_categories_ids': [category.id],
            'supply_method_ids': [method.id],
        })

        src_location = self.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        dest_location = self.env['stock.location'].search([('usage', '=', 'customer')], limit=1)

        move = self.env['stock.move'].create({
            'reference': 'Test Stock Move',
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': 5.0,
            'location_id': src_location.id,
            'location_dest_id': dest_location.id,
            'supply_id': request.id,
        })

        self.assertEqual(move.supply_id, request)
