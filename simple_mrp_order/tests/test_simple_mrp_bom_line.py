# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ATHUL RAJ B S(<https://www.cybrosys.com>)
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

class TestSimpleMRPBomLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSimpleMRPBomLine, cls).setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Component',
            'is_storable': True,
        })
        cls.bom = cls.env['simple.mrp.bom'].create({
            'product_id': cls.env['product.product'].create({'name': 'Final'}).id,
            'product_qty': 1.0,
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
        })

    def test_bom_line_creation(self):
        """Test BOM line creation"""
        line = self.env['simple.mrp.bom.line'].create({
            'product_id': self.product.id,
            'product_qty': 10.0,
            'uom_id': self.product.uom_id.id,
            'bom_id': self.bom.id,
        })
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.product_qty, 10.0)
        self.assertEqual(line.bom_id, self.bom)
