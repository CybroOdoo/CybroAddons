# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductProduct(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestProductProduct, cls).setUpClass()
        cls.product_1 = cls.env['product.product'].create({
            'name': 'Component Product 1',
            'type': 'consu',
        })
        cls.product_2 = cls.env['product.product'].create({
            'name': 'Component Product 2',
            'type': 'consu',
        })

    def test_action_create_bom(self):
        """Test action_create_bom on product.product returns correct wizard action"""
        products = self.product_1 + self.product_2
        # Set active_ids in context to simulate selection from tree/form view
        action = products.with_context(active_ids=products.ids).action_create_bom()
        self.assertEqual(action.get('name'), "Create BOM")
        self.assertEqual(action.get('res_model'), "product.bom")
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('target'), 'new')
        self.assertEqual(action.get('context', {}).get('default_product_ids'), products.ids)
