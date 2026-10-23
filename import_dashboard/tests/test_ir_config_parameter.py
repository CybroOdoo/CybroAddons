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

from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestIrConfigParameter(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ConfigParam = self.env['ir.config_parameter']

    def test_create_validation_error(self):
        """Test that enabling a feature without the required module installed raises a ValidationError"""
        att_module = self.env['ir.module.module'].search([('name', '=', 'hr_attendance')], limit=1)
        if att_module and att_module.state == 'installed':
            with patch.object(type(self.env['ir.module.module']), 'search', return_value=self.env['ir.module.module']):
                with self.assertRaises(ValidationError):
                    self.ConfigParam.create({
                        'key': 'import_dashboard.import_attendance',
                        'value': 'True'
                    })
        else:
            with self.assertRaises(ValidationError):
                self.ConfigParam.create({
                    'key': 'import_dashboard.import_attendance',
                    'value': 'True'
                })

    def test_write_validation_error(self):
        """Test that writing True on an existing param without required module raises ValidationError"""
        key = 'import_dashboard.import_attendance'
        param = self.ConfigParam.search([('key', '=', key)], limit=1)
        if param:
            param.write({'value': 'False'})
        else:
            param = self.ConfigParam.create({'key': key, 'value': 'False'})
        att_module = self.env['ir.module.module'].search([('name', '=', 'hr_attendance')], limit=1)
        if att_module and att_module.state == 'installed':
            with patch.object(type(self.env['ir.module.module']), 'search', return_value=self.env['ir.module.module']):
                with self.assertRaises(ValidationError):
                    param.write({'value': 'True'})
        else:
            with self.assertRaises(ValidationError):
                param.write({'value': 'True'})

    def test_check_user_group(self):
        """Test that check_user_group returns the expected keys"""
        res = self.ConfigParam.check_user_group()
        expected_keys = [
            'bill_of_material', 'pos', 'import_attendance', 'import_payment',
            'import_task', 'import_sale', 'import_purchase', 'import_product_template',
            'import_partner', 'import_invoice', 'import_pricelist', 'import_vendor_pricelist'
        ]
        for key in expected_keys:
            self.assertIn(key, res)
