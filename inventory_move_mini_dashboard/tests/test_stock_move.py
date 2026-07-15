# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj (<https://www.cybrosys.com>)
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
############################################################################


from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase

class TestInventoryDashboard(TransactionCase):

    def setUp(self):
        super().setUp()

        # Use an existing product to bypass database constraint issues in the test environment
        self.product = self.env['product.product'].search([('type', '=', 'product')], limit=1)

        self.location_src = self.env.ref('stock.stock_location_stock')
        self.location_dest = self.env.ref('stock.stock_location_customers')

        states = [
            'draft',
            'cancel',
            'waiting',
            'partially_available',
            'assigned',
            'done',
        ]

        self.moves = self.env['stock.move']

        # Capture initial dashboard values before creating moves to account for existing database records
        self.initial_dashboard = self.env['stock.move'].retrieve_inventory_dashboard()

        for state in states:
            move = self.env['stock.move'].create({
                'name': f'Test Move {state}',
                'product_id': self.product.id,
                'product_uom_qty': 10,
                'product_uom': self.product.uom_id.id,
                'location_id': self.location_src.id,
                'location_dest_id': self.location_dest.id,
                'date': fields.Datetime.now(),
            })

            move.state = state
            self.moves |= move

    def test_retrieve_inventory_dashboard(self):

        result = self.env['stock.move'].retrieve_inventory_dashboard()

        self.assertIsInstance(result, dict)
        self.assertEqual(result['draft'], self.initial_dashboard['draft'] + 1)
        self.assertEqual(result['cancelled'], self.initial_dashboard['cancelled'] + 1)
        self.assertEqual(result['waiting'], self.initial_dashboard['waiting'] + 1)
        self.assertEqual(result['partially_available'], self.initial_dashboard['partially_available'] + 1)
        self.assertEqual(result['assigned'], self.initial_dashboard['assigned'] + 1)
        self.assertEqual(result['done'], self.initial_dashboard['done'] + 1)

        self.assertEqual(result['count'], self.initial_dashboard['count'] + 6)
        self.assertGreaterEqual(result['average_products'], 0)
