# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
from odoo import api, fields, models


class HrEmployee(models.Model):
    """Inherited the model hr employee for adding gym trainer field."""
    _inherit = 'hr.employee'

    is_trainer = fields.Boolean(string='Gym Trainer',
                                help="The employee is trainer")

    gym_skill_ids = fields.Many2many(
        'hr.skill',
        relation='hr_employee_gym_skill_rel',
        column1='employee_id',
        column2='skill_id',
        string='Gym Specializations',
        compute='_compute_gym_skills',
        store=True,
        help="Gym-related skills of the trainer (read-only display)"
    )

    @api.depends('skill_ids', 'skill_ids.is_gym_skill')
    def _compute_gym_skills(self):
        """Get only gym-related skills from all employee skills"""
        for employee in self:
            employee.gym_skill_ids = employee.skill_ids.filtered('is_gym_skill')
