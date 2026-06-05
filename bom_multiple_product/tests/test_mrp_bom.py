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
class TestMrpBom(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestMrpBom, cls).setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Finished Product',
            'type': 'consu',
        })
        cls.bom = cls.env['mrp.bom'].create({
            'product_id': cls.product.id,
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
        })

    def test_action_select_products(self):
        """Test action_select_products returns the correct wizard action"""
        action = self.bom.action_select_products()
        self.assertEqual(action.get('name'), "Select Products")
        self.assertEqual(action.get('res_model'), "bom.products")
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('target'), 'new')
        self.assertEqual(action.get('context', {}).get('default_bom_id'), self.bom.id)
