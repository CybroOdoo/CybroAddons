# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aleena K (odoo@cybrosys.com)
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
"""Unit test suite for website index and follow module."""
from unittest.mock import patch
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.website_sale.tests.common import MockRequest
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.index_and_follow.controllers.index_and_follow import (
    WebIndex,
    WebIndexJson,
)


@tagged('post_install', '-at_install', 'index_and_follow')
class TestIndexAndFollow(TransactionCase):
    """Test cases for the Website Index and Follow module."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for product and user."""
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'Test Index Product',
            'list_price': 50.0,
        })
        cls.public_user = cls.env.ref('base.public_user')

    def test_01_is_index_default_true(self):
        """Test that is_index defaults to True on a newly created product."""
        self.assertTrue(self.product.is_index,
                        "is_index should default to True.")

    def test_02_is_index_write_false(self):
        """Test that is_index can be set to False."""
        self.product.write({'is_index': False})
        self.assertFalse(self.product.is_index,
                         "is_index should be False after writing False.")

    def test_03_is_index_write_true(self):
        """Test that is_index can be set back to True."""
        self.product.write({'is_index': False})
        self.product.write({'is_index': True})
        self.assertTrue(self.product.is_index,
                        "is_index should be True after writing True.")

    def test_04_controller_web_index_authorized(self):
        """Test the WebIndexJson controller with an authorized internal user."""
        controller = WebIndexJson()
        with MockRequest(self.env):
            # 1. Update is_index to False
            res = controller.web_index(index=False, product=self.product.id)
            self.assertEqual(res, {'success': True})
            self.assertFalse(self.product.is_index)

            # 2. Update is_index to True
            res = controller.web_index(index=True, product=self.product.id)
            self.assertEqual(res, {'success': True})
            self.assertTrue(self.product.is_index)

            # 3. Call with non-existent product ID
            res = controller.web_index(index=True, product=9999999)
            self.assertEqual(res, {'success': True})

    def test_05_controller_web_index_unauthorized(self):
        """Test the WebIndexJson controller with an unauthorized user."""
        controller = WebIndexJson()
        with MockRequest(self.env(user=self.public_user)):
            res = controller.web_index(index=False, product=self.product.id)
            self.assertEqual(res, {'error': 'Access Denied'})
            self.assertTrue(self.product.is_index)

    def test_06_controller_prepare_product_values(self):
        """Test WebIndex._prepare_product_values controller method."""
        controller = WebIndex()
        with MockRequest(self.env), \
             patch.object(WebsiteSale, '_prepare_product_values',
                          return_value={'base_key': 'base_val'}):
            # pylint: disable=protected-access
            values = controller._prepare_product_values(self.product, category=None)
            self.assertEqual(values.get('base_key'), 'base_val')
            self.assertTrue(values.get('page_index'))
            self.assertEqual(values.get('product_rec'), self.product)
            self.assertTrue(values.get('user'))

            # Test passing a category
            values_cat = controller._prepare_product_values(self.product, category='test_categ')
            self.assertEqual(values_cat.get('base_key'), 'base_val')

    def test_07_views_structure(self):
        """Test view inheritance and architecture for index and follow templates."""
        # 1. Test portal index_follow view
        view_meta = self.env.ref('index_and_follow.index_follow')
        self.assertTrue(view_meta.active)
        self.assertEqual(view_meta.inherit_id, self.env.ref('portal.frontend_layout'))
        self.assertIn('robots', view_meta.arch_base)
        self.assertIn('noindex, nofollow', view_meta.arch_base)

        # 2. Test website_index view
        view_cta = self.env.ref('index_and_follow.website_index')
        self.assertTrue(view_cta.active)
        self.assertEqual(view_cta.inherit_id, self.env.ref('website_sale.cta_wrapper'))
        self.assertIn('is_index', view_cta.arch_base)

    def test_08_access_rights(self):
        """Test that access rules for product.template are defined in ir.access."""
        access_records = self.env['ir.access'].search([
            ('model_id.model', '=', 'product.template'),
        ])
        self.assertTrue(
            access_records,
            "Access rights for product.template must be defined.",
        )
        # Verify access record defined by index_and_follow
        access_user = self.env.ref(
            'index_and_follow.access_product_template_user',
            raise_if_not_found=False,
        )
        self.assertTrue(
            access_user,
            "index_and_follow.access_product_template_user must exist.",
        )
        self.assertEqual(access_user.model_id.model, 'product.template')
        self.assertEqual(access_user.operation, 'crud')

