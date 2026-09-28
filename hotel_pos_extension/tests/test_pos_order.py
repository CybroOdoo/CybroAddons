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
class TestPosOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'POS Test Partner'})
        cls.pricelist = cls.env['product.pricelist'].create({'name': 'Test Pricelist'})
        cls.booking = cls.env['room.booking'].create({
            'partner_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
        })
        # Locate/create POS session helper
        cls.session = cls.env['pos.session'].search([('state', '=', 'opened')], limit=1)
        if not cls.session:
            pos_config = cls.env['pos.config'].search([], limit=1)
            if not pos_config:
                # Find main company's default journal
                journal = cls.env['account.journal'].search([('type', '=', 'general')], limit=1)
                pos_config = cls.env['pos.config'].create({
                    'name': 'Test POS shop config',
                    'journal_id': journal.id if journal else False,
                })
            cls.session = cls.env['pos.session'].create({
                'config_id': pos_config.id,
                'user_id': cls.env.user.id,
            })

    def test_compute_hotel_pos_status(self):
        """Test calculation of hotel_pos_status field on pos.order."""
        order = self.env['pos.order'].create({
            'session_id': self.session.id,
            'partner_id': self.partner.id,
            'amount_total': 100.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
            'state': 'draft',
        })
        self.assertEqual(order.hotel_pos_status, 'draft')

    def test_ensure_hotel_pos_line(self):
        """Test hotel pos line gets created for rooms linkage."""
        order = self.env['pos.order'].create({
            'session_id': self.session.id,
            'partner_id': self.partner.id,
            'booking_id': self.booking.id,
            'amount_total': 120.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
            'state': 'draft',
        })
        pos_lines = self.env['hotel.pos.line'].search([('pos_order_id', '=', order.id)])
        self.assertEqual(len(pos_lines), 1)
        self.assertEqual(pos_lines.booking_id, self.booking)
        self.assertEqual(pos_lines.state, 'draft')
