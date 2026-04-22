# -*- coding: utf-8 -*-
#############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class ProjectTaskType(models.Model):
    """
    Extends 'project.task.type' to support HSE work permit requirements and 
    ensure only one 'Waiting' stage exists.
    """
    _inherit = 'project.task.type'

    is_work_permit_required = fields.Boolean('Is Work Permit Required',
                                             help='Enable if this stage requires any work permit approval.')
    is_waiting_stage = fields.Boolean("Is Waiting Stage",
                                      help="Enable this when is waiting stage applies.")

    def write(self, vals):
        """
        Overrides write to ensure only one stage is marked as the 'Waiting' stage.
        """
        res = super().write(vals)

        if vals.get('is_waiting_stage'):
            for rec in self:
                if rec.is_waiting_stage:
                    other_stages = self.search([
                        ('id', '!=', rec.id),
                        ('is_waiting_stage', '=', True)
                    ])
                    other_stages.write({'is_waiting_stage': False})

        return res

    @api.constrains('is_waiting_stage')
    def _check_waiting_stage(self):
        """ Ensures only one 'Waiting' stage exists."""
        for rec in self:
            if rec.is_waiting_stage:
                other_stages = self.search([
                    ('id', '!=', rec.id),
                    ('is_waiting_stage', '=', True)
                ])
                if other_stages:
                    raise ValidationError(
                        _("Only one 'Waiting' stage can exist at a time."))
