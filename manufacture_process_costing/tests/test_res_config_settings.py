# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestResConfigSettings(TransactionCase):

    def test_process_costing_method_config_parameter(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'manufacture_process_costing.process_costing_method',
            'work-center',
        )

        values = self.env['res.config.settings'].default_get([
            'process_costing_method'])
        self.assertEqual(values['process_costing_method'], 'work-center')
