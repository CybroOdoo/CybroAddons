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

class TestProductAddVendor(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_template = cls.env['product.template'].create({
            'name': 'Test Vendor Product',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Vendor Partner',
        })
        cls.currency = cls.env.ref('base.USD')

    def test_add_product_vendors(self):
        wizard = self.env['product.add.vendor'].create({
            'product_ids': [self.product_template.id],
        })
        self.env['product.vendor'].create({
            'wizard_id': wizard.id,
            'partner_id': self.partner.id,
            'price': 150.0,
            'delay': 5,
            'currency_id': self.currency.id,
        })
        wizard.action_add_product_vendors()
        
        self.assertEqual(len(self.product_template.seller_ids), 1)
        seller = self.product_template.seller_ids[0]
        self.assertEqual(seller.partner_id, self.partner)
        self.assertEqual(seller.price, 150.0)
        self.assertEqual(seller.delay, 5)
        self.assertEqual(seller.currency_id, self.currency)
