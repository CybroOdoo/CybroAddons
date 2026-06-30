import sys
import odoo
from odoo.tests.common import TransactionCase
import unittest

class TestConfig(TransactionCase):
    def test_config(self):
        self.env['res.config.settings'].create({'is_restricted': False}).execute()
        val = self.env['ir.config_parameter'].sudo().get_param('restrict_pricelist_user.is_restricted')
        print(f"VAL FALSE: {repr(val)}")
        
        self.env['res.config.settings'].create({'is_restricted': True}).execute()
        val = self.env['ir.config_parameter'].sudo().get_param('restrict_pricelist_user.is_restricted')
        print(f"VAL TRUE: {repr(val)}")

loader = unittest.TestLoader()
suite = loader.loadTestsFromTestCase(TestConfig)
runner = unittest.TextTestRunner()
# runner.run(suite)
