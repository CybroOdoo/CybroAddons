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
from odoo.tests import common, tagged
from odoo.exceptions import UserError
import base64


@tagged('post_install', '-at_install')
class TestProductTemplate(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'Test AR Product',
        })

    def test_onchange_model_ar_valid_glb(self):
        """Test that setting a valid .glb file creates an attachment."""
        self.product.write({
            'filename': 'model.glb',
            'model_ar': base64.b64encode(b'glb_content'),
        })
        self.product._onchange_model_ar()

        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'product.template'),
            ('res_id', '=', self.product.id),
            ('name', '=', 'model.glb'),
        ])
        self.assertTrue(attachment, "Attachment should have been created")
        self.assertEqual(attachment.datas, base64.b64encode(b'glb_content'))

    def test_onchange_model_ar_valid_gltf(self):
        """Test that setting a valid .gltf file creates an attachment."""
        self.product.write({
            'filename': 'model.gltf',
            'model_ar': base64.b64encode(b'gltf_content'),
        })
        self.product._onchange_model_ar()

        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'product.template'),
            ('res_id', '=', self.product.id),
            ('name', '=', 'model.gltf'),
        ])
        self.assertTrue(attachment, "Attachment should have been created")
        self.assertEqual(attachment.datas, base64.b64encode(b'gltf_content'))

    def test_onchange_model_ar_invalid(self):
        """Test that setting an invalid extension raises UserError."""
        self.product.write({
            'filename': 'model.png',
            'model_ar': base64.b64encode(b'image_content'),
        })
        with self.assertRaises(UserError):
            self.product._onchange_model_ar()

    def test_onchange_model_ar_empty(self):
        """Test that when model_ar is empty, no action is taken."""
        self.product.write({
            'filename': 'model.glb',
            'model_ar': False,
        })
        self.product._onchange_model_ar()
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'product.template'),
            ('res_id', '=', self.product.id),
        ])
        self.assertFalse(attachment, "No attachment should be created when model_ar is empty")
