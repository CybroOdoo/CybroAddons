# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo.tests import TransactionCase

class TestMaterialUsed(TransactionCase):
    """ TestMaterialUsed tests """

    def setUp(self):
        """ Setup method """
        super(TestMaterialUsed, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Material',
            'lst_price': 100.0,
        })

    def test_onchange_material_product_id(self):
        """ Test _onchange_material_product_id function """
        material = self.env['material.used'].new({
            'material_product_id': self.product.id
        })
        material._onchange_material_product_id()
        self.assertEqual(material.price, 100.0, "Price should be updated from product lst_price")
