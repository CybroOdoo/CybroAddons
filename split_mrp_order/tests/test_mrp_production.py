# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies <https://www.cybrosys.com>.
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
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestMrpProduction(TransactionCase):

    def setUp(self):
        super(TestMrpProduction, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'is_storable': True,
        })
        self.mo = self.env['mrp.production'].create({
            'product_id': self.product.id,
            'product_qty': 10,
        })

    def test_01_action_split_order_valid(self):
        """Test action_split_order returns a wizard action for valid qty."""
        action = self.mo.action_split_order()
        self.assertEqual(action['res_model'], 'split.order')
        self.assertEqual(action['context']['default_order_id'], self.mo.id)

    def test_02_action_split_order_invalid(self):
        """Test action_split_order raises UserError for qty <= 1."""
        self.mo.product_qty = 1
        with self.assertRaises(UserError):
            self.mo.action_split_order()
