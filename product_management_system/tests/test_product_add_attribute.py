# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase

class TestProductAddAttribute(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_template = cls.env['product.template'].create({
            'name': 'Test Attribute Product',
        })
        cls.attribute = cls.env['product.attribute'].create({
            'name': 'Color',
        })
        cls.value_red = cls.env['product.attribute.value'].create({
            'name': 'Red',
            'attribute_id': cls.attribute.id,
        })
        cls.value_blue = cls.env['product.attribute.value'].create({
            'name': 'Blue',
            'attribute_id': cls.attribute.id,
        })

    def test_add_product_attributes(self):
        wizard = self.env['product.add.attribute'].create({
            'product_ids': [self.product_template.id],
        })
        self.env['product.management.attribute'].create({
            'wizard_id': wizard.id,
            'attribute_id': self.attribute.id,
            'value_ids': [self.value_red.id, self.value_blue.id],
        })
        wizard.action_add_product_attributes()
        
        self.assertEqual(len(self.product_template.attribute_line_ids), 1)
        attr_line = self.product_template.attribute_line_ids[0]
        self.assertEqual(attr_line.attribute_id, self.attribute)
        self.assertIn(self.value_red, attr_line.value_ids)
        self.assertIn(self.value_blue, attr_line.value_ids)
