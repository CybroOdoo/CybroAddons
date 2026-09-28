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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

@tagged('post_install', '-at_install')
class TestRoomBookingExtension(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Booking Test Partner'})
        cls.pricelist = cls.env['product.pricelist'].create({'name': 'Test Pricelist'})
        cls.booking = cls.env['room.booking'].create({
            'partner_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
        })
        # Locate/setup simple POS session
        cls.session = cls.env['pos.session'].search([('state', '=', 'opened')], limit=1)
        if not cls.session:
            pos_config = cls.env['pos.config'].search([], limit=1)
            cls.session = cls.env['pos.session'].create({
                'config_id': pos_config.id if pos_config else False,
                'user_id': cls.env.user.id,
            })

    def test_room_booking_pos_amounts(self):
        """Test calculation of POS amounts and presence flags on room.booking."""
        order = self.env['pos.order'].create({
            'session_id': self.session.id,
            'partner_id': self.partner.id,
            'booking_id': self.booking.id,
            'amount_total': 180.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
            'state': 'draft',
        })
        self.booking._compute_has_pos_orders()
        self.assertTrue(self.booking.has_pos_orders)

        self.booking._compute_amount_total_pos()
        self.assertEqual(self.booking.amount_total_pos, 180.0)

    def test_bill_summary_lines(self):
        """Test summary retrieval for the bill report QWeb templates."""
        order = self.env['pos.order'].create({
            'session_id': self.session.id,
            'partner_id': self.partner.id,
            'booking_id': self.booking.id,
            'amount_total': 250.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
            'state': 'draft',
        })
        lines = self.booking.get_bill_summary_lines()
        self.assertTrue(any(line['total'] == 250.0 for line in lines))

    def test_action_compute_bill(self):
        """Test that action_compute_bill triggers compute.bill window action."""
        action = self.booking.action_compute_bill()
        self.assertEqual(action.get('res_model'), 'compute.bill')
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
