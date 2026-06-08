# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
import base64
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestExcalidrawAttachWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner for Sketch',
        })
        cls.partner_model = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)

        # 1x1 Transparent PNG base64 string
        cls.dummy_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    def test_01_get_chatter_models(self):
        """Test _get_chatter_models returns valid models including res.partner."""
        wizard = self.env['excalidraw.attach.wizard'].create({
            'sketch_data': self.dummy_png_base64,
            'model_id': self.partner_model.id,
            'res_id': self.partner.id,
        })
        allowed = wizard._get_chatter_models()
        self.assertIn('res.partner', allowed)
        # Verify allowed models possess message_ids field
        for m in allowed:
            self.assertIn('message_ids', self.env[m]._fields)

    def test_02_action_attach_validations(self):
        """Test validation warnings returned when model or record is invalid."""
        wizard = self.env['excalidraw.attach.wizard'].create({
            'sketch_data': self.dummy_png_base64,
            'model_id': self.partner_model.id,
            'res_id': 0, # Invalid res_id
        })
        # Force model_name to empty
        wizard.write({'model_id': False})
        res = wizard.action_attach()
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(res['tag'], 'display_notification')
        self.assertEqual(res['params']['type'], 'danger')
        self.assertEqual(res['params']['message'], 'Please select a valid model.')

        # Set valid model, but invalid res_id
        wizard.write({
            'model_id': self.partner_model.id,
            'res_id': 999999,
        })
        res = wizard.action_attach()
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(res['tag'], 'display_notification')
        self.assertEqual(res['params']['type'], 'danger')
        self.assertEqual(res['params']['message'], 'Selected record does not exist.')

    def test_03_action_attach_image(self):
        """Test attaching drawing as an image."""
        wizard = self.env['excalidraw.attach.wizard'].create({
            'sketch_data': self.dummy_png_base64,
            'attachment_type': 'image',
            'model_id': self.partner_model.id,
            'res_id': self.partner.id,
        })
        res = wizard.action_attach()
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(res['tag'], 'display_notification')
        self.assertEqual(res['params']['type'], 'success')

        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.partner.id),
        ], limit=1)
        self.assertTrue(attachment)
        self.assertEqual(attachment.mimetype, 'image/png')
        self.assertTrue(attachment.datas)

    def test_04_action_attach_pdf(self):
        """Test attaching drawing converted to PDF."""
        wizard = self.env['excalidraw.attach.wizard'].create({
            'sketch_data': self.dummy_png_base64,
            'attachment_type': 'pdf',
            'model_id': self.partner_model.id,
            'res_id': self.partner.id,
        })
        res = wizard.action_attach()
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(res['tag'], 'display_notification')
        self.assertEqual(res['params']['type'], 'success')

        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.partner.id),
            ('mimetype', '=', 'application/pdf'),
        ], limit=1)
        self.assertTrue(attachment)
        self.assertEqual(attachment.name[-4:], '.pdf')

    def test_05_action_attach_excel(self):
        """Test attaching drawing converted to Excel."""
        wizard = self.env['excalidraw.attach.wizard'].create({
            'sketch_data': self.dummy_png_base64,
            'attachment_type': 'excel',
            'model_id': self.partner_model.id,
            'res_id': self.partner.id,
        })
        res = wizard.action_attach()
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(res['tag'], 'display_notification')
        self.assertEqual(res['params']['type'], 'success')

        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.partner.id),
            ('mimetype', '=', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        ], limit=1)
        self.assertTrue(attachment)
        self.assertEqual(attachment.name[-5:], '.xlsx')

    def test_06_action_attach_word(self):
        """Test attaching drawing converted to Word."""
        wizard = self.env['excalidraw.attach.wizard'].create({
            'sketch_data': self.dummy_png_base64,
            'attachment_type': 'word',
            'model_id': self.partner_model.id,
            'res_id': self.partner.id,
        })
        res = wizard.action_attach()
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(res['tag'], 'display_notification')
        self.assertEqual(res['params']['type'], 'success')

        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.partner.id),
            ('mimetype', '=', 'application/msword'),
        ], limit=1)
        self.assertTrue(attachment)
        self.assertEqual(attachment.name[-4:], '.doc')

    def test_07_convert_sketch_format(self):
        """Test convert_sketch_format utility returns valid data dictionaries for all types."""
        wizard = self.env['excalidraw.attach.wizard']

        # Image conversion
        res = wizard.convert_sketch_format(self.dummy_png_base64, 'image')
        self.assertEqual(res['mimetype'], 'image/png')
        self.assertEqual(res['data'], self.dummy_png_base64)

        # PDF conversion
        res = wizard.convert_sketch_format(self.dummy_png_base64, 'pdf')
        self.assertEqual(res['mimetype'], 'application/pdf')

        # Excel conversion
        res = wizard.convert_sketch_format(self.dummy_png_base64, 'excel')
        self.assertEqual(res['mimetype'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        # Word conversion
        res = wizard.convert_sketch_format(self.dummy_png_base64, 'word')
        self.assertEqual(res['mimetype'], 'application/msword')
        # Word returns HTML wrapping the image
        decoded_html = base64.b64decode(res['data']).decode('utf-8')
        self.assertIn('Sketch Drawing', decoded_html)
        self.assertIn(self.dummy_png_base64, decoded_html)
