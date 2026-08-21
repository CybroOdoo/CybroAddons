# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Safa KB (<https://www.cybrosys.com>)
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
################################################################################
from datetime import timedelta
from odoo import fields
from odoo.tests import common
from odoo.exceptions import ValidationError

class TestProductVendorUpdate(common.TransactionCase):

    def setUp(self):
        super(TestProductVendorUpdate, self).setUp()
        self.vendor = self.env.user.partner_id
        self.product_1 = self.env['product.template'].create({
            'name': 'Test Product 1',
            'type': 'consu'
        })
        self.product_2 = self.env['product.template'].create({
            'name': 'Test Product 2',
            'type': 'consu'
        })

    def test_action_update_vendor(self):
        wizard = self.env['product.vendor.update'].with_context(active_ids=[self.product_1.id, self.product_2.id]).create({
            'partner_id': self.vendor.id,
            'price_unit': 100.0,
            'lead_time': 5,
            'quantity': 10,
            'vendor_product_name': 'Vendor Product Name',
            'vendor_product_code': 'VPC001',
            'validity_from': fields.Date.today(),
            'validity_to': fields.Date.today() + timedelta(days=365)
        })
        wizard.action_update_vendor()

        for product in [self.product_1, self.product_2]:
            self.assertEqual(len(product.seller_ids), 1)
            seller = product.seller_ids[0]
            self.assertEqual(seller.partner_id, self.vendor)
            self.assertEqual(seller.price, 100.0)
            self.assertEqual(seller.delay, 5)
            self.assertEqual(seller.min_qty, 10.0)
            self.assertEqual(seller.product_name, 'Vendor Product Name')
            self.assertEqual(seller.product_code, 'VPC001')

    def test_onchange_validity_to(self):
        with self.assertRaises(ValidationError):
            wizard = self.env['product.vendor.update'].create({
                'partner_id': self.vendor.id,
                'validity_from': fields.Date.today() + timedelta(days=10),
                'validity_to': fields.Date.today()
            })
            wizard._onchange_validity_to()
