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
class TestProjectProject(TransactionCase):
    """Test suite for custom methods on project.project."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({
            'name': 'Test Performance Dashboard Project',
        })

    def test_get_color_code_format(self):
        """Verify that get_color_code returns a valid hexadecimal color string."""
        color = self.project.get_color_code()
        self.assertIsInstance(color, str, "Color code must be a string")
        self.assertEqual(len(color), 7, "Hex color code must be exactly 7 characters (#RRGGBB)")
        self.assertTrue(color.startswith('#'), "Hex color code must start with '#'")
        # Ensure the trailing 6 characters are valid hex
        hex_val = int(color[1:], 16)
        self.assertTrue(0 <= hex_val <= 0xFFFFFF, "Color hex value must be in range 0x000000 - 0xFFFFFF")

    def test_get_color_code_randomness(self):
        """Verify that multiple calls produce valid hex colors."""
        colors = {self.project.get_color_code() for _ in range(20)}
        self.assertGreater(len(colors), 1, "Color codes should be randomly generated across calls")
        for c in colors:
            self.assertEqual(len(c), 7)
            self.assertTrue(c.startswith('#'))
            int(c[1:], 16)
