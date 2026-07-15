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

# -*- coding: utf-8 -*-


from odoo import fields
from odoo.tests.common import TransactionCase



class TestStockPickingDashboard(TransactionCase):
    """Test cases for stock picking dashboard"""

    def setUp(self):
        super().setUp()

        self.stock_picking = self.env['stock.picking']

        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
        })



        self.incoming_type = self.env.ref('stock.picking_type_in')
        self.outgoing_type = self.env.ref('stock.picking_type_out')
        self.internal_type = self.env.ref('stock.picking_type_internal')

        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.customer_location = self.env.ref(
            'stock.stock_location_customers'
        )

        self.initial_dashboard = self.stock_picking.stock_picking_dashboard()

        self._create_pickings()

    def _create_pickings(self):
        """Create test pickings"""

        picking_data = [
            ('Receipt Done', self.incoming_type, 'done'),
            ('Delivery Done', self.outgoing_type, 'done'),
            ('Internal Done', self.internal_type, 'done'),
            ('Draft Picking', self.outgoing_type, 'draft'),
            ('Waiting Picking', self.outgoing_type, 'waiting'),
            ('Assigned Picking', self.outgoing_type, 'assigned'),
            ('Cancelled Picking', self.outgoing_type, 'cancel'),
        ]

        for name, picking_type, state in picking_data:
            picking = self.stock_picking.create({
                'name': name,
                'partner_id': self.partner.id,
                'picking_type_id': picking_type.id,
                'location_id': self.stock_location.id,
                'location_dest_id': self.customer_location.id,
            })

            # Force state for testing
            picking.write({'state': state})

            if state == 'done':
                picking.date_done = fields.Datetime.now()

    def test_stock_picking_dashboard(self):
        """Test stock picking dashboard values"""

        result = self.stock_picking.stock_picking_dashboard()

        self.assertIsInstance(result, dict)

        self.assertEqual(result['draft'], self.initial_dashboard['draft'] + 1)
        self.assertEqual(result['waiting'], self.initial_dashboard['waiting'] + 1)
        self.assertEqual(result['assigned'], self.initial_dashboard['assigned'] + 1)
        self.assertEqual(result['cancel'], self.initial_dashboard['cancel'] + 1)

        self.assertEqual(result['receipts'], self.initial_dashboard['receipts'] + 1)
        self.assertEqual(result['outgoing'], self.initial_dashboard['outgoing'] + 1)
        self.assertEqual(result['internal'], self.initial_dashboard['internal'] + 1)

        self.assertEqual(result['done'], self.initial_dashboard['done'] + 3)
