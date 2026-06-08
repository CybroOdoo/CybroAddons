# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Surya Gayathry TA (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestAccountMove(TransactionCase):
    def setUp(self):
        super(TestAccountMove, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu', 'is_storable': True,
        })
        self.picking_type_out = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
        self.picking_type_in = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)

        self.account_move_out = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'picking_type_id': self.picking_type_out.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 100.0,
            })]
        })

    def test_get_stock_type_ids(self):
        # The method _get_stock_type_ids is used as default value
        move_out = self.env['account.move'].with_context(default_move_type='out_invoice').create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
        })
        self.assertEqual(move_out.picking_type_id.code, 'outgoing')

        move_in = self.env['account.move'].with_context(default_move_type='in_invoice').create({
            'partner_id': self.partner.id,
            'move_type': 'in_invoice',
        })
        self.assertEqual(move_in.picking_type_id.code, 'incoming')

    def test_action_stock_move(self):
        # Create stock move from invoice
        self.account_move_out.action_stock_move()
        self.assertTrue(self.account_move_out.invoice_picking_id)
        self.assertEqual(self.account_move_out.picking_count, 1)
        self.assertEqual(self.account_move_out.invoice_picking_id.picking_type_id.code, 'outgoing')
        
        # Test error if no picking type
        self.account_move_out.picking_type_id = False
        with self.assertRaises(UserError):
            self.account_move_out.action_stock_move()

    def test_action_view_picking(self):
        self.account_move_out.action_stock_move()
        res = self.account_move_out.action_view_picking()
        self.assertEqual(res['res_model'], 'stock.picking')
        self.assertEqual(res['res_id'], self.account_move_out.invoice_picking_id.id)

    def test_reverse_moves(self):
        _logger.info("Starting test_reverse_moves")
        self.account_move_out.action_post()
        # Create reverse move (credit note)
        reverse_move = self.account_move_out._reverse_moves()
        self.assertEqual(reverse_move.picking_type_id.code, 'incoming')
