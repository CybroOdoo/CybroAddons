# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
from odoo.tests.common import TransactionCase

class TestMultipleReference(TransactionCase):

    def setUp(self):
        super(TestMultipleReference, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'is_storable': True,
        })
        self.ReferenceModel = self.env['multiple.reference.per.product']

    def test_01_create_reference(self):
        """Test creating a multiple reference for a product"""
        ref = self.ReferenceModel.create({
            'multiple_references_name': 'REF123',
            'product_id': self.product.id,
        })
        self.assertEqual(ref.multiple_references_name, 'REF123')
        self.assertEqual(ref.product_id.id, self.product.id)

    def test_02_action_set_as_default(self):
        """Test setting a reference as default code"""
        ref = self.ReferenceModel.create({
            'multiple_references_name': 'DEF456',
            'product_id': self.product.id,
        })
        ref.action_set_as_default()
        self.assertEqual(self.product.default_code, 'DEF456')
        self.assertTrue(ref.is_default_reference)

    def test_03_update_product_default_code(self):
        """Test that updating default_code creates a reference for the old one"""
        self.product.default_code = 'OLD789'
        self.product.write({'default_code': 'NEW012'})
        old_ref = self.ReferenceModel.search([
            ('multiple_references_name', '=', 'OLD789'),
            ('product_id', '=', self.product.id)
        ])
        self.assertTrue(bool(old_ref))
        self.assertEqual(old_ref.multiple_references_name, 'OLD789')
