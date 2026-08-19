# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase

class TestPurchaseOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if 'purchase.order' not in cls.env:
            return
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner PO'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product PO',
            'type': 'consu',
        })

    def test_01_create_picking(self):
        """Test that _create_picking triggers correctly."""
        if 'purchase.order' not in self.env:
            return
        
        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_qty': 1.0,
                    'price_unit': 100.0,
                })
            ]
        })
        po.button_confirm()
        self.assertTrue(po.picking_ids, "Picking should be generated for PO")
