# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shikhil Raj (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests import HttpCase, new_test_user, tagged
from odoo.tools import BinaryBytes


@tagged('post_install', '-at_install')
class TestModelViewerWidget(HttpCase):
    """Test the 3D model of the products, in the backend and in the browser."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env, login='model_user', groups='base.group_user')
        cls.product = cls.env['product.template'].create(
            {'name': '3D Test Product'})

    def test_product_form_uses_the_viewer(self):
        arch = self.env['product.template'].get_view(
            self.env.ref('product.product_template_only_form_view').id,
            'form')['arch']
        self.assertIn('widget="model_3d_viewer"', arch)

    def test_model_is_stored_as_an_attachment(self):
        self.product.model_3d = BinaryBytes(b'glTF', filename='model.glb')
        attachment = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'product.template'),
            ('res_id', '=', self.product.id),
            ('res_field', '=', 'model_3d'),
        ])
        self.assertEqual(len(attachment), 1)

    def test_internal_user_can_read_the_model(self):
        self.product.model_3d = BinaryBytes(b'glTF', filename='model.glb')
        self.assertEqual(
            self.product.with_user(self.user).model_3d.content, b'glTF')

    def test_saved_model_is_served_to_the_viewer(self):
        self.product.model_3d = BinaryBytes(b'glTF', filename='model.glb')
        self.authenticate('model_user', 'model_user')
        response = self.url_open(
            f'/web/image/product.template/{self.product.id}/model_3d')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'glTF')

    def test_model_viewer_tour(self):
        self.start_tour(f'/odoo/product.template/{self.product.id}',
                        'model_viewer_widget_tour', login='admin')
        self.assertTrue(self.product.model_3d)
