# -*- coding: utf-8 -*-
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestWebsitePreLoaderStyleController(HttpCase):

    def setUp(self):
        super(TestWebsitePreLoaderStyleController, self).setUp()
        self.IrConfigParameter = self.env['ir.config_parameter'].sudo()

    def test_loader_config_route(self):
        """Test the loader_config JSON route."""
        # Set config parameters
        self.IrConfigParameter.set_param('website_pre_loader_style.enable_website_pre_loader', 'True')
        self.IrConfigParameter.set_param('website_pre_loader_style.loader_style', 'cube')

        response_data = self.make_jsonrpc_request('/website_pre_loader_style/loader_config', {})
        
        self.assertTrue(response_data.get('enabled'), "Enabled should be True")
        self.assertEqual(response_data.get('loader_style'), 'cube', "Style should be cube")

        # Update and retest
        self.IrConfigParameter.set_param('website_pre_loader_style.enable_website_pre_loader', 'False')
        self.IrConfigParameter.set_param('website_pre_loader_style.loader_style', 'spinner')

        response_data_update = self.make_jsonrpc_request('/website_pre_loader_style/loader_config', {})
        self.assertFalse(response_data_update.get('enabled'), "Enabled should be False")
        self.assertEqual(response_data_update.get('loader_style'), 'spinner', "Style should be spinner")
