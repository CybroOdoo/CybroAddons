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

class TestProductChangeTracking(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_template_1 = cls.env['product.template'].create({
            'name': 'Track Product 1',
            'is_storable': True,
            'tracking': 'none',
        })
        cls.product_template_2 = cls.env['product.template'].create({
            'name': 'Track Product 2',
            'is_storable': True,
            'tracking': 'none',
        })

    def test_change_product_tracking_lot(self):
        wizard = self.env['product.change.tracking'].create({
            'product_ids': [self.product_template_1.id, self.product_template_2.id],
            'tracking': 'lot',
        })
        wizard.action_change_product_tracking()
        self.assertTrue(self.product_template_1.is_storable)
        self.assertEqual(self.product_template_1.tracking, 'lot')
        self.assertTrue(self.product_template_2.is_storable)
        self.assertEqual(self.product_template_2.tracking, 'lot')

    def test_change_product_tracking_disable(self):
        wizard = self.env['product.change.tracking'].create({
            'product_ids': [self.product_template_1.id, self.product_template_2.id],
            'tracking': 'disable',
        })
        wizard.action_change_product_tracking()
        self.assertFalse(self.product_template_1.is_storable)
        self.assertFalse(self.product_template_2.is_storable)
