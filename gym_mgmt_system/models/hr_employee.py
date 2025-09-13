# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _


class HrEmployee(models.Model):
    """Inherited the model hr employee for adding gym trainer field."""
    _inherit = 'hr.employee'

    is_trainer = fields.Boolean(string='Gym Trainer',
                                help="The employee is trainer")

    gym_skill_ids = fields.Many2many(
        'hr.skill',
        string='Gym Specializations',
        compute='_compute_gym_skills',
        help="Gym-related skills of the trainer (read-only display)"
    )

    exercise_for_ids = fields.Many2many("exercise.for",
                                        string="Exercise For",
                                        help='For which part this exercise')

    @api.depends('skill_ids')
    def _compute_gym_skills(self):
        """Get only gym-related skills from all employee skills"""
        for employee in self:
            try:
                if employee.skill_ids:
                    gym_skills = employee.skill_ids.filtered(
                        lambda emp_skill: emp_skill.skill_id and emp_skill.skill_id.skill_type_id.is_gym_skill
                    )
                    employee.gym_skill_ids = gym_skills.mapped('skill_id')
                else:
                    employee.gym_skill_ids = False
            except Exception:
                employee.gym_skill_ids = False


class HrSkillType(models.Model):
    """Extend HR Skill Type for gym category"""
    _inherit = 'hr.skill.type'

    is_gym_skill = fields.Boolean(string='Is Gym Skill', default=False)


class HrSkill(models.Model):
    """Extend HR Skill for gym skills"""
    _inherit = 'hr.skill'

    is_gym_skill = fields.Boolean(related='skill_type_id.is_gym_skill', store=True)
