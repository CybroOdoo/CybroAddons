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
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test suite for res.config.settings signup points configuration."""

    def test_sign_up_points(self):
        """Test setting and getting sign_up_points config parameter."""
        settings = self.env['res.config.settings'].create({
            'sign_up_points': 25.0,
        })
        settings.execute()
        param_value = self.env['ir.config_parameter'].sudo().get_str(
            'refer_friend_and_earn.sign_up_points', default=0)
        self.assertEqual(float(param_value or 0), 25.0)
