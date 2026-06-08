# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestWebsiteProductStock(common.TransactionCase):

    def setUp(self):
        super(TestWebsiteProductStock, self).setUp()
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.customer_location = self.env.ref('stock.stock_location_customers')
        self.product = self.env['product.product'].create({
            'name': 'Test Stock Product',
            'type': 'consu',
            'is_storable': True,
        })
        self.template = self.product.product_tmpl_id
        self.env['ir.default'].sudo().search([
            ('field_id.model', '=', 'product.template'),
            ('field_id.name', 'in', ['location_type', 'stock_location_id', 'stock_type']),
        ]).unlink()

    def _create_done_move(self, qty, src, dest):
        move = self.env['stock.move'].create({
            'product_id': self.product.id,
            'product_uom_qty': qty,
            'product_uom': self.product.uom_id.id,
            'location_id': src.id,
            'location_dest_id': dest.id,
        })
        move.quantity = qty
        move._action_confirm()
        move._action_assign()
        move.picked = True
        move._action_done()
        return move

    def _calc_specific_qty(self, location, stock_type='on_hand'):
        if stock_type == 'on_hand':
            incoming = self.env['stock.move'].sudo().search([
                ('product_id', '=', self.product.id),
                ('location_dest_id', '=', location.id),
                ('state', '=', 'done'),
            ])
            outgoing = self.env['stock.move'].sudo().search([
                ('product_id', '=', self.product.id),
                ('location_id', '=', location.id),
                ('state', '=', 'done'),
            ])
        else:
            incoming = self.env['stock.move'].sudo().search([
                ('product_id', '=', self.product.id),
                ('location_dest_id', '=', location.id),
            ])
            outgoing = self.env['stock.move'].sudo().search([
                ('product_id', '=', self.product.id),
                ('location_id', '=', location.id),
            ])
        return sum(m.product_uom_qty for m in incoming) - sum(m.product_uom_qty for m in outgoing)

    def test_01_location_type_selection(self):
        options = self.template._get_location_type_selection()
        keys = [k for k, _ in options]
        self.assertIn('all', keys)
        self.assertIn('specific', keys)

    def test_02_stock_type_selection(self):
        options = self.template._get_stock_type_selection()
        keys = [k for k, _ in options]
        self.assertIn('on_hand', keys)
        self.assertIn('forecast', keys)

    def test_03_default_location_type_field(self):
        self.assertIn(self.template.location_type, ['all', 'specific', False])

    def test_04_default_stock_type_field(self):
        self.assertIn(self.template.stock_type, ['on_hand', 'forecast', False])

    def test_05_set_location_type_all(self):
        self.template.write({'location_type': 'all'})
        self.assertEqual(self.template.location_type, 'all')

    def test_06_set_location_type_specific(self):
        self.template.write({'location_type': 'specific', 'stock_location_id': self.stock_location.id})
        self.assertEqual(self.template.location_type, 'specific')
        self.assertEqual(self.template.stock_location_id.id, self.stock_location.id)

    def test_07_set_stock_type_on_hand(self):
        self.template.write({'stock_type': 'on_hand'})
        self.assertEqual(self.template.stock_type, 'on_hand')

    def test_08_set_stock_type_forecast(self):
        self.template.write({'stock_type': 'forecast'})
        self.assertEqual(self.template.stock_type, 'forecast')

    def test_09_specific_location_incoming_done(self):
        self._create_done_move(10, self.customer_location, self.stock_location)
        qty = self._calc_specific_qty(self.stock_location, 'on_hand')
        self.assertEqual(qty, 10)

    def test_10_specific_location_outgoing_done(self):
        self._create_done_move(10, self.customer_location, self.stock_location)
        self._create_done_move(4, self.stock_location, self.customer_location)
        qty = self._calc_specific_qty(self.stock_location, 'on_hand')
        self.assertEqual(qty, 6)

    def test_11_specific_location_net_zero(self):
        self._create_done_move(5, self.customer_location, self.stock_location)
        self._create_done_move(5, self.stock_location, self.customer_location)
        qty = self._calc_specific_qty(self.stock_location, 'on_hand')
        self.assertEqual(qty, 0)

    def test_12_all_location_qty_available(self):
        self._create_done_move(7, self.customer_location, self.stock_location)
        self.template.write({'location_type': 'all', 'stock_type': 'on_hand'})
        self.assertEqual(self.template.stock_type, 'on_hand')
        self.assertGreaterEqual(self.product.qty_available, 0)

    def test_13_ir_default_location_type(self):
        self.env['ir.default'].set('product.template', 'location_type', 'all')
        val = self.env['ir.default']._get('product.template', 'location_type')
        self.assertEqual(val, 'all')

    def test_14_ir_default_stock_type(self):
        self.env['ir.default'].set('product.template', 'stock_type', 'forecast')
        val = self.env['ir.default']._get('product.template', 'stock_type')
        self.assertEqual(val, 'forecast')

    def test_15_ir_default_stock_location(self):
        self.env['ir.default'].set('product.template', 'stock_location_id', self.stock_location.id)
        val = self.env['ir.default']._get('product.template', 'stock_location_id')
        self.assertEqual(val, self.stock_location.id)
