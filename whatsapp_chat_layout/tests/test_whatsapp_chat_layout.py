# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import base64
import json

from odoo.tests import HttpCase, tagged
from odoo.tools.binary import BinaryBytes


@tagged('post_install', '-at_install')
class TestWhatsappChatLayout(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.valid_png_base64 = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        cls.valid_png_binary = BinaryBytes(base64.b64decode(cls.valid_png_base64))

    def setUp(self):
        super().setUp()
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user_chat',
            'password': 'test_password',
            'email': 'test@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })

        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_str('whatsapp_chat_layout.background_color', '#123456')
        ICP.set_str('whatsapp_chat_layout.layout_color', '#654321')

        self.test_user.company_id.background_image = self.valid_png_binary
        self.env.flush_all()

    def test_res_config_settings(self):
        """Test reading and writing settings fields."""
        settings = self.env['res.config.settings'].create({
            'background_color': '#AABBCC',
            'layout_color': '#DDEEFF',
            'chat_background': self.valid_png_binary,
        })
        settings.execute()

        ICP = self.env['ir.config_parameter'].sudo()
        self.assertEqual(ICP.get_str('whatsapp_chat_layout.background_color'), '#AABBCC')
        self.assertEqual(ICP.get_str('whatsapp_chat_layout.layout_color'), '#DDEEFF')
        self.assertTrue(self.env.company.background_image)

    def test_res_company_background_image(self):
        """Test setting and getting background_image on res.company."""
        company = self.env.company
        company.background_image = self.valid_png_binary
        self.assertTrue(company.background_image)

    def test_get_color_jsonrpc(self):
        """Test the /select_color JSON-RPC route."""
        self.authenticate('test_user_chat', 'test_password')

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {},
            "id": 1,
        }

        response = self.url_open('/select_color', data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200, "The request should be successful")

        result_data = json.loads(response.text)
        self.assertIn('result', result_data, "Response should contain a 'result' key")

        result = result_data['result']
        self.assertEqual(result.get('background_color'), '#123456', "Background color should match the configured parameter")
        self.assertEqual(result.get('layout_color'), '#654321', "Layout color should match the configured parameter")
        self.assertTrue(result.get('background_image'), "Background image should be present")

    def test_get_user_image_jsonrpc(self):
        """Test the /select_user_image JSON-RPC route."""
        self.test_user.partner_id.image_1920 = self.valid_png_binary
        self.env.flush_all()

        self.authenticate('test_user_chat', 'test_password')

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {},
            "id": 2,
        }

        response = self.url_open('/select_user_image', data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200, "The request should be successful")

        result_data = json.loads(response.text)
        self.assertIn('result', result_data, "Response should contain a 'result' key")

        result = result_data['result']
        self.assertTrue(result, "Result should contain the user's image data")
