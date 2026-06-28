# -*- coding: utf-8 -*-
import json
from odoo.tests.common import HttpCase, tagged
import logging

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestMasterSearch(HttpCase):

    def setUp(self):
        super(TestMasterSearch, self).setUp()
        _logger.info("Setting up TestMasterSearch environment")

        self.test_partner_name = "Master Search Unique Test Partner"

        # Open a new cursor to write and commit changes so the HTTP thread can see them
        new_cr = self.env.registry.cursor()
        try:
            new_env = self.env(cr=new_cr)
            
            # Reset admin user's password to 'admin'
            admin_user = new_env.ref('base.user_admin')
            admin_user.write({'password': 'admin'})
            _logger.info("Admin password reset to 'admin' on new cursor")

            # Create a unique test partner to search for
            partner = new_env['res.partner'].create({
                'name': self.test_partner_name,
                'email': 'mstest@example.com',
            })
            _logger.info("Test partner created: %s (ID: %s) on new cursor", partner.name, partner.id)
            
            new_cr.commit()
            self.partner_id = partner.id
            _logger.info("setUp changes committed successfully")
        finally:
            new_cr.close()

        # Retrieve the base module record (read-only is fine on standard cursor)
        self.base_module = self.env['ir.module.module'].search([('name', '=', 'base')], limit=1)
        _logger.info("Base module retrieved: %s (ID: %s)", self.base_module.name, self.base_module.id)
        _logger.info("setUp completed successfully")

    def tearDown(self):
        _logger.info("Cleaning up TestMasterSearch environment")
        if hasattr(self, 'partner_id') and self.partner_id:
            new_cr = self.env.registry.cursor()
            try:
                new_env = self.env(cr=new_cr)
                partner = new_env['res.partner'].browse(self.partner_id)
                if partner.exists():
                    partner.unlink()
                    new_cr.commit()
                    _logger.info("Test partner (ID: %s) deleted and committed via new cursor", self.partner_id)
            finally:
                new_cr.close()
        super(TestMasterSearch, self).tearDown()

    def test_res_config_settings(self):
        """Test retrieving and saving master search settings."""
        _logger.info("Running test_res_config_settings")

        # Create configuration wizard
        config_wizard = self.env['res.config.settings'].create({
            'master_search_installed_ids': [(6, 0, [self.base_module.id])],
        })
        _logger.info("Config settings wizard created with base module")

        # Execute set_values
        config_wizard.execute()
        _logger.info("Config settings saved")

        # Retrieve parameter and assert it was stored correctly
        stored_param = self.env['ir.config_parameter'].sudo().get_param('master_search_systray.master_search_installed_ids')
        _logger.info("Stored config parameter: %s", stored_param)
        self.assertIsNotNone(stored_param, "Config parameter should be stored")
        self.assertIn(str(self.base_module.id), stored_param, "Base module ID should be in stored config parameter")

        # Create new config wizard and test get_values
        new_wizard = self.env['res.config.settings'].create({})
        values = new_wizard.get_values()
        _logger.info("get_values returned: %s", values)
        self.assertIn('master_search_installed_ids', values, "get_values should contain master_search_installed_ids")
        self.assertIn(self.base_module.id, values['master_search_installed_ids'][0][2], "Base module ID should be in get_values output")

        _logger.info("test_res_config_settings completed successfully")

    def test_controller_search(self):
        """Test the master search controller via json-rpc request."""
        _logger.info("Running test_controller_search")

        # Set config settings to include base module
        self.env['ir.config_parameter'].sudo().set_param(
            'master_search_systray.master_search_installed_ids',
            str([self.base_module.id])
        )
        _logger.info("Config settings parameter configured directly for test")

        # Authenticate as admin user
        admin_login = self.env.ref('base.user_admin').login
        self.authenticate(admin_login, 'admin')
        _logger.info("Authenticated successfully as admin user '%s'", admin_login)

        # Send post request to controller
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "query": self.test_partner_name,
            },
            "id": 1,
        }
        _logger.info("Sending JSON-RPC request to /master/search with payload: %s", payload)

        from unittest.mock import patch
        partner_model = self.env['ir.model'].search([('model', '=', 'res.partner')])

        with patch('odoo.addons.base.models.ir_model.IrModel.search', return_value=partner_model):
            response = self.url_open(
                url="/master/search",
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
        
        _logger.info("Response received with status code: %s", response.status_code)
        self.assertEqual(response.status_code, 200, "Response status should be 200")

        result_data = response.json()
        _logger.info("JSON response: %s", result_data)
        
        self.assertIn('result', result_data, "Response should contain a result field")
        result = result_data['result']
        
        # Verify that we received the partner record in search results
        found = False
        for group in result:
            for item in group:
                if item.get('model') == 'res.partner' and item.get('name') == self.test_partner_name:
                    found = True
                    _logger.info("Found matching test partner in search results: ID %s", item.get('id'))
                    break
        
        self.assertTrue(found, "Test partner should be found in controller search results")
        _logger.info("test_controller_search completed successfully")
