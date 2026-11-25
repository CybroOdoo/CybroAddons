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
"""Test Suite for Custom Robots.txt."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCustomRobotsTxt(TransactionCase):
    """Test suite for custom robots.txt modes on website and wizard"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and active website."""
        super().setUpClass()
        cls.website = cls.env.website or cls.env['website'].search([], limit=1)

    def test_website_mode_field(self):
        """Test mode field on website model"""
        self.website.mode = 'allow_all'
        self.assertEqual(self.website.mode, 'allow_all')
        self.website.mode = 'disallow_all'
        self.assertEqual(self.website.mode, 'disallow_all')
        self.website.mode = 'custom'
        self.assertEqual(self.website.mode, 'custom')

    def test_wizard_default_mode(self):
        """Test wizard initializes with current website mode"""
        self.website.mode = 'disallow_all'
        wizard = self.env['website.robots'].create({})
        self.assertEqual(wizard.mode, 'disallow_all')

    def test_wizard_onchange_allow_all(self):
        """Test onchange when mode is set to allow_all"""
        wizard = self.env['website.robots'].create({'mode': 'allow_all'})
        wizard._onchange_mode()
        self.assertEqual(wizard.content, "User-agent: *\nAllow: /")

    def test_wizard_onchange_disallow_all(self):
        """Test onchange when mode is set to disallow_all"""
        wizard = self.env['website.robots'].create({'mode': 'disallow_all'})
        wizard._onchange_mode()
        self.assertEqual(wizard.content, "User-agent: *\nDisallow: /")

    def test_wizard_onchange_custom_with_empty_content(self):
        """Test onchange when mode is custom and website robots_txt is empty"""
        self.website.robots_txt = False
        wizard = self.env['website.robots'].create({'mode': 'custom'})
        wizard._onchange_mode()
        self.assertEqual(wizard.content, " ")

    def test_wizard_onchange_custom_with_existing_content(self):
        """Test onchange when mode is custom and website robots_txt exists"""
        self.website.robots_txt = "User-agent: Googlebot\nDisallow: /admin"
        wizard = self.env['website.robots'].create({'mode': 'custom'})
        wizard._onchange_mode()
        self.assertEqual(wizard.content, self.website.robots_txt)

    def test_wizard_action_save(self):
        """Test saving wizard updates website mode and robots_txt content"""
        wizard = self.env['website.robots'].create({
            'mode': 'allow_all',
            'content': "User-agent: *\nAllow: /",
        })
        res = wizard.action_save()
        self.assertEqual(res.get('type'), 'ir.actions.act_window_close')
        self.assertEqual(self.website.mode, 'allow_all')
        self.assertEqual(self.website.robots_txt, "User-agent: *\nAllow: /")
