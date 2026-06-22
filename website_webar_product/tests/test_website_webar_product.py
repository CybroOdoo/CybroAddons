# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aleena K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests import tagged, HttpCase
import base64


@tagged('post_install', '-at_install')
class TestWebsiteWebarProductController(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'Test Controller Product',
            'enable_ar_images': True,
            'ar_image_type': 'upload',
            'filename': 'model.glb',
            'ar_scale': 'fixed',
            'auto_rotate': True,
            'ar_placement': 'wall',
        })
        # Create an attachment that matches the product AR model upload
        cls.attachment = cls.env['ir.attachment'].create({
            'name': 'model.glb',
            'datas': base64.b64encode(b'glb_content_controller'),
            'res_model': 'product.template',
            'res_id': cls.product.id,
        })

    def test_get_product_ar_model(self):
        """Test the get_product_ar_model endpoint return values."""
        res = self.make_jsonrpc_request(
            '/product/ar_image',
            params={'product_id': self.product.id}
        )

        self.assertEqual(res['type'], 'upload')
        self.assertEqual(res['ar_scale'], 'fixed')
        self.assertEqual(res['auto_rotate'], True)
        self.assertEqual(res['ar_placement'], 'wall')
        self.assertEqual(res['ar_url'], False)
        self.assertTrue(res['local_url'].startswith('/web/image/'))
