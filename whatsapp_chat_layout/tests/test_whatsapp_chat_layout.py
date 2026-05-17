# -*- coding: utf-8 -*-
from odoo.tests import HttpCase, tagged
import json

@tagged('post_install', '-at_install')
class TestWhatsappChatLayout(HttpCase):

    def setUp(self):
        super(TestWhatsappChatLayout, self).setUp()
        
        # Create a dedicated test user with a known password
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user_chat',
            'password': 'test_password',
            'email': 'test@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        
        # Set some configuration parameters
        self.env['ir.config_parameter'].sudo().set_param('whatsapp_chat_layout.background_color', '#123456')
        self.env['ir.config_parameter'].sudo().set_param('whatsapp_chat_layout.layout_color', '#654321')
        
        # Set a dummy background image for the company (valid 1x1 PNG)
        self.valid_png_base64 = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        self.test_user.company_id.background_image = self.valid_png_base64

    def test_get_color_jsonrpc(self):
        """Test the /select_color JSON-RPC route"""
        self.authenticate('test_user_chat', 'test_password')
        
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {},
            "id": 1
        }
        
        response = self.url_open('/select_color', data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200, "The request should be successful")
        
        # Parse JSON response
        result_data = json.loads(response.text)
        self.assertIn('result', result_data, "Response should contain a 'result' key")
        
        result = result_data['result']
        self.assertEqual(result.get('background_color'), '#123456', "Background color should match the configured parameter")
        self.assertEqual(result.get('layout_color'), '#654321', "Layout color should match the configured parameter")
        
        # The background image is verified by checking it returns a value or the right string, 
        # Odoo might format binary fields dynamically.
        self.assertTrue(result.get('background_image'), "Background image should be present")

    def test_get_user_image_jsonrpc(self):
        """Test the /select_user_image JSON-RPC route"""
        # Set a dummy image for the user's partner (valid 1x1 PNG)
        self.test_user.partner_id.image_1920 = self.valid_png_base64
        
        self.authenticate('test_user_chat', 'test_password')
        
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {},
            "id": 2
        }
        
        response = self.url_open('/select_user_image', data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200, "The request should be successful")
        
        result_data = json.loads(response.text)
        self.assertIn('result', result_data, "Response should contain a 'result' key")
        
        result = result_data['result']
        self.assertTrue(result, "Result should contain the user's image data")
