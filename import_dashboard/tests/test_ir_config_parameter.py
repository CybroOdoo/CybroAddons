# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestIrConfigParameter(TransactionCase):

    def setUp(self):
        super(TestIrConfigParameter, self).setUp()
        self.ConfigParam = self.env['ir.config_parameter']

    def test_create_validation_error(self):
        """Test that enabling a feature without the required module installed raises a ValidationError"""
        # We need a key that requires a module not installed. 
        # Assuming hr_attendance might not be installed in all test environments
        # but let's use one we can verify existence of.
        with self.assertRaises(ValidationError):
            self.ConfigParam.create({
                'key': 'import_dashboard.import_attendance',
                'value': 'True'
            })

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
