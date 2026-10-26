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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestVolunteerSkill(TransactionCase):
    """Test cases for 'volunteer.skill' model in volunteers_donors_management."""

    def test_default_color(self):
        """Test _default_color returns an integer between 1 and 11."""
        # 1. Direct function call
        color = self.env['volunteer.skill']._default_color()
        self.assertIsInstance(color, int)
        self.assertGreaterEqual(color, 1)
        self.assertLessEqual(color, 11)

        # 2. Field default assignment on record creation
        skill = self.env['volunteer.skill'].create({
            'volunteer_skill': 'Medical Aid',
            'volunteer_skill_code': 'MED_01',
        })
        self.assertIsInstance(skill.color, int)
        self.assertGreaterEqual(skill.color, 1)
        self.assertLessEqual(skill.color, 11)
