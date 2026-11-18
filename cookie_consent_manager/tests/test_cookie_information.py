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
class TestCookieInformation(TransactionCase):
    """Unit tests for the cookie.information model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cookie_info = cls.env['cookie.information'].create({
            'template_title': 'Standard Cookie Template',
            'pop_up_text': 'We use cookies on our website.',
            'cookie_color': 5,
            'is_change_pop_up_position': True,
            'is_change_pop_up_position_top': True,
            'pop_up_position_top': 'top_left',
            'accept_btn_txt': 'Accept All',
            'reject_btn_txt': 'Reject All',
            'cookie_policy_btn': 'View Policy',
        })

    def test_get_color(self):
        """Test _get_color method for mapping color IDs to hex codes."""
        self.assertEqual(self.cookie_info._get_color(0), "#FFFFFF")
        self.assertEqual(self.cookie_info._get_color(1), "#FF0000")
        self.assertEqual(self.cookie_info._get_color(5), "#800080")
        self.assertEqual(self.cookie_info._get_color(11), "#4B0082")
        # Unmapped or invalid color should fallback to white
        self.assertEqual(self.cookie_info._get_color(999), "#FFFFFF")

    def test_onchange_is_change_pop_up_position(self):
        """Test _onchange_is_change_pop_up_position when disabling custom position."""
        record = self.cookie_info
        record.is_change_pop_up_position = False
        record._onchange_is_change_pop_up_position()
        self.assertFalse(record.is_change_pop_up_position_top)
        self.assertFalse(record.is_change_pop_up_position_bottom)
        self.assertFalse(record.pop_up_position_top)
        self.assertFalse(record.pop_up_position_bottom)

    def test_onchange_is_change_pop_up_position_top(self):
        """Test _onchange_is_change_pop_up_position_top resets bottom position."""
        record = self.cookie_info
        record.is_change_pop_up_position_bottom = True
        record.pop_up_position_bottom = 'bottom_center'
        record.is_change_pop_up_position_top = True
        record._onchange_is_change_pop_up_position_top()
        self.assertFalse(record.is_change_pop_up_position_bottom)
        self.assertFalse(record.pop_up_position_bottom)

    def test_onchange_is_change_pop_up_position_bottom(self):
        """Test _onchange_is_change_pop_up_position_bottom resets top position."""
        record = self.cookie_info
        record.is_change_pop_up_position_top = True
        record.pop_up_position_top = 'top_center'
        record.is_change_pop_up_position_bottom = True
        record._onchange_is_change_pop_up_position_bottom()
        self.assertFalse(record.is_change_pop_up_position_top)
        self.assertFalse(record.pop_up_position_top)

    def test_cookie_information_create(self):
        """Test creating a template and verifying stored values."""
        template = self.env['cookie.information'].create({
            'template_title': 'Bottom Cookie Template',
            'pop_up_text': 'Cookie consent message',
            'cookie_color': 10,
            'is_change_pop_up_position': True,
            'is_change_pop_up_position_bottom': True,
            'pop_up_position_bottom': 'bottom_right',
            'accept_btn_txt': 'I Agree',
            'reject_btn_txt': 'Decline',
            'cookie_policy_btn': 'Privacy Info',
        })
        self.assertEqual(template.template_title, 'Bottom Cookie Template')
        self.assertEqual(template.pop_up_position_bottom, 'bottom_right')
        self.assertEqual(template.accept_btn_txt, 'I Agree')
        self.assertEqual(template.reject_btn_txt, 'Decline')
