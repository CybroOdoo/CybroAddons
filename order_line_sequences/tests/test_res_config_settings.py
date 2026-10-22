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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test suite for res.config.settings order line sequences."""

    def test_show_sol_numbers_related_field(self):
        """Test show_sol_numbers is properly related to company setting."""
        settings = self.env['res.config.settings'].create({})
        self.assertEqual(
            settings.show_sol_numbers,
            self.env.company.show_sol_numbers,
        )

    def test_show_sol_numbers_reflects_company_value(self):
        """Test settings show_sol_numbers reflects company changes."""
        self.env.company.show_sol_numbers = False
        settings_false = self.env['res.config.settings'].create({})
        self.assertFalse(settings_false.show_sol_numbers)

        self.env.company.show_sol_numbers = True
        settings_true = self.env['res.config.settings'].create({})
        self.assertTrue(settings_true.show_sol_numbers)
