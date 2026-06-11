# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestVolunteerSkill(TransactionCase):
    """Unit tests for the VolunteerSkills model (_default_color)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.volunteer_skill_model = cls.env['volunteer.skill']

    def test_default_color_is_integer(self):
        """Test that _default_color returns an integer between 1 and 11."""
        skill = self.volunteer_skill_model.create({
            'volunteer_skill': 'Test Skill',
            'volunteer_skill_code': 'TSK01',
        })
        self.assertIsInstance(skill.color, int)
        self.assertGreaterEqual(skill.color, 1)
        self.assertLessEqual(skill.color, 11)

    def test_create_volunteer_skill(self):
        """Test creating a volunteer skill record with all fields."""
        skill = self.volunteer_skill_model.create({
            'volunteer_skill': 'Python Programming',
            'volunteer_skill_code': 'PY01',
            'description': '<p>Python language skills</p>',
        })
        self.assertEqual(skill.volunteer_skill, 'Python Programming')
        self.assertEqual(skill.volunteer_skill_code, 'PY01')

    def test_default_color_multiple_skills_in_range(self):
        """Test that multiple created skills all receive colors in range 1-11."""
        for i in range(5):
            skill = self.volunteer_skill_model.create({
                'volunteer_skill': f'Skill {i}',
                'volunteer_skill_code': f'SK0{i}',
            })
            self.assertGreaterEqual(skill.color, 1)
            self.assertLessEqual(skill.color, 11)
