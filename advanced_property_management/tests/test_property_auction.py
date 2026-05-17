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
from odoo.exceptions import ValidationError
from odoo import fields

class TestPropertyAuction(TransactionCase):

    def setUp(self):
        super(TestPropertyAuction, self).setUp()
        self.user = self.env.user
        self.partner1 = self.env['res.partner'].create({'name': 'Bidder 1'})
        self.partner2 = self.env['res.partner'].create({'name': 'Bidder 2'})
        self.property = self.env['property.property'].create({
            'name': 'Auction Property',
            'property_type': 'residential',
            'street': 'Auction Street',
            'country_id': self.env.ref('base.in').id,
            'sale_rent': 'for_auction',
            'state': 'available',
        })
        self.now = fields.Datetime.now()
        self.auction = self.env['property.auction'].create({
            'property_id': self.property.id,
            'responsible_id': self.user.id,
            'start_time': fields.Datetime.add(self.now, minutes=-5),
            'end_time': fields.Datetime.add(self.now, minutes=5),
            'bid_start_price': 10000,
        })

    def test_auction_creation(self):
        """Test sequence generation on creation"""
        self.assertNotEqual(self.auction.auction_seq, 'New')

    def test_time_constraints(self):
        """Test start and end time constraints"""
        with self.assertRaises(ValidationError):
            self.auction.write({
                'start_time': fields.Datetime.add(self.now, hours=2),
                'end_time': fields.Datetime.add(self.now, hours=1),
            })
        
        # Test out of current time range (not between start and end)
        # Note: self.now is current, so it should be valid initially.
        # But if we set start_time to future:
        with self.assertRaises(ValidationError):
            self.auction.write({
                'start_time': fields.Datetime.add(self.now, hours=3),
                'end_time': fields.Datetime.add(self.now, hours=4),
            })

    def test_state_transitions(self):
        """Test auction state transitions"""
        self.auction.action_confirm()
        self.assertEqual(self.auction.state, 'confirmed')
        self.auction.action_start()
        self.assertEqual(self.auction.state, 'started')
        self.auction.action_cancel()
        self.assertEqual(self.auction.state, 'canceled')

    def test_auction_end_and_winner(self):
        """Test action_end logic and winner selection"""
        self.env['property.auction.line'].create({
            'auction_id': self.auction.id,
            'partner_id': self.partner1.id,
            'bid_amount': 15000,
        })
        self.env['property.auction.line'].create({
            'auction_id': self.auction.id,
            'partner_id': self.partner2.id,
            'bid_amount': 20000,
        })
        
        self.auction.action_end()
        self.assertEqual(self.auction.state, 'ended')
        self.assertEqual(self.auction.auction_winner_id.id, self.partner2.id)
        self.assertEqual(self.auction.final_price, 20000)

    def test_create_sale_order(self):
        """Test action_create_sale_order logic"""
        self.auction.auction_winner_id = self.partner2.id
        self.auction.final_price = 20000
        self.auction.action_create_sale_order()
        self.assertTrue(self.auction.sold)
        
        sale = self.env['property.sale'].search([('property_id', '=', self.property.id)])
        self.assertTrue(sale)
        self.assertEqual(sale.partner_id.id, self.partner2.id)
        self.assertEqual(sale.sale_price, 20000)
