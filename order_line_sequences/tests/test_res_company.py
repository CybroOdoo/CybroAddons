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
from collections import deque

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.order_line_sequences import post_init_hook


@tagged('post_install', '-at_install')
class TestResCompany(TransactionCase):
    """Test suite for res.company line numbers configuration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({
            'name': 'Test Company Sequences',
        })

    def test_default_show_sol_numbers(self):
        """Test show_sol_numbers is True by default on new companies."""
        self.assertTrue(self.company.show_sol_numbers)

    def test_auto_init_enables_show_sol_numbers(self):
        """Test _auto_init sets show_sol_numbers to True if False."""
        self.company.write({'show_sol_numbers': False})
        self.assertFalse(self.company.show_sol_numbers)
        queue_created = False
        if not hasattr(self.env.registry, '_post_init_queue'):
            self.env.registry._post_init_queue = deque()
            queue_created = True
        try:
            self.company._auto_init()
        finally:
            if (
                queue_created
                and hasattr(self.env.registry, '_post_init_queue')
            ):
                del self.env.registry._post_init_queue
        self.company.invalidate_recordset(['show_sol_numbers'])
        self.assertTrue(self.company.show_sol_numbers)

    def test_post_init_hook(self):
        """Test post_init_hook enables show_sol_numbers for companies."""
        self.company.write({'show_sol_numbers': False})
        self.assertFalse(self.company.show_sol_numbers)
        post_init_hook(self.env)
        self.company.invalidate_recordset(['show_sol_numbers'])
        self.assertTrue(self.company.show_sol_numbers)
