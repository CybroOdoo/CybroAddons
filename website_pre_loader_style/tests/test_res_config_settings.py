# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWebsitePreLoaderStyleConfig(TransactionCase):

    def setUp(self):
        super(TestWebsitePreLoaderStyleConfig, self).setUp()
        self.ResConfigSettings = self.env['res.config.settings']
        self.IrConfigParameter = self.env['ir.config_parameter'].sudo()

    def test_default_config_settings(self):
        """Test the default values of website pre-loader configuration."""
        config = self.ResConfigSettings.create({
            'enable_website_pre_loader': True,
            'loader_style': 'dual',
        })
        config.execute()

        enabled = self.IrConfigParameter.get_param('website_pre_loader_style.enable_website_pre_loader')
        style = self.IrConfigParameter.get_param('website_pre_loader_style.loader_style')
        
        self.assertEqual(enabled, 'True', "Enable preloader should be saved as 'True'")
        self.assertEqual(style, 'dual', "Loader style should be saved as 'dual'")
        
        config_update = self.ResConfigSettings.create({
            'enable_website_pre_loader': False,
            'loader_style': 'cube',
        })
        config_update.execute()
        
        enabled_update = self.IrConfigParameter.get_param('website_pre_loader_style.enable_website_pre_loader')
        style_update = self.IrConfigParameter.get_param('website_pre_loader_style.loader_style')
        
        self.assertFalse(enabled_update, "Enable preloader should be falsy after being disabled")
        self.assertEqual(style_update, 'cube', "Loader style should be saved as 'cube'")
