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

from odoo.tests import common


class TestMrpProduction(common.TransactionCase):
    """
    Test suite for verifying POS order linking fields on MRP production orders.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'MRP Test Product',
            'type': 'consu',
        })
        cls.component = cls.env['product.product'].create({
            'name': 'MRP Test Component',
            'type': 'consu',
        })
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'product_id': cls.product.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [(0, 0, {
                'product_id': cls.component.id,
                'product_qty': 1.0,
            })],
        })
        cls.pos_config = cls.env.ref('point_of_sale.pos_config_main', raise_if_not_found=False)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].search([], limit=1)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].create({
                'name': 'Test POS Config',
            })
        cls.session = cls.env['pos.session'].search([
            ('config_id', '=', cls.pos_config.id),
            ('state', '=', 'opened')
        ], limit=1)
        if not cls.session:
            cls.session = cls.env['pos.session'].create({
                'config_id': cls.pos_config.id,
                'user_id': cls.env.uid,
            })

    def test_01_mrp_production_pos_order_fields(self):
        """Test that pos_order_id and pos_order_line_id fields can be stored and searched on mrp.production."""
        pos_order = self.env['pos.order'].create({
            'session_id': self.session.id,
            'name': 'Manual POS Order',
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'qty': 1.0,
                'price_unit': 10.0,
                'price_subtotal': 10.0,
                'price_subtotal_incl': 10.0,
            })],
            'amount_total': 10.0,
            'amount_tax': 0.0,
            'amount_paid': 10.0,
            'amount_return': 0.0,
        })
        line = pos_order.lines[0]

        mrp_order = self.env['mrp.production'].create({
            'product_id': self.product.id,
            'product_qty': 1.0,
            'bom_id': self.bom.id,
            'pos_order_id': pos_order.id,
            'pos_order_line_id': line.id,
        })

        self.assertEqual(mrp_order.pos_order_id.id, pos_order.id)
        self.assertEqual(mrp_order.pos_order_line_id.id, line.id)
        self.assertIn(mrp_order, pos_order.mrp_production_ids)
        self.assertEqual(pos_order.mrp_production_count, 1)

        # Searchability test
        found = self.env['mrp.production'].search([('pos_order_id', '=', pos_order.id)])
        self.assertEqual(found.id, mrp_order.id)
