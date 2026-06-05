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
class TestProductTemplate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestProductTemplate, cls).setUpClass()
        cls.template = cls.env['product.template'].create({
            'name': 'Finished Product Template',
            'type': 'consu',
        })

    def test_action_create_bom(self):
        """Test action_create_bom on product.template returns correct wizard action"""
        action = self.template.action_create_bom()
        self.assertEqual(action.get('name'), "Create BOM")
        self.assertEqual(action.get('res_model'), "product.bom")
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('target'), 'new')
        self.assertEqual(
            action.get('context', {}).get('default_product_ids'),
            self.template.product_variant_ids.ids
        )
