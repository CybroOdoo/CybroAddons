# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class ProjectStageUpdate(models.TransientModel):
    """ Wizard for updating project stage """
    _name = "project.stage.update"
    _description = 'Project stage mass update'

    is_update_stage = fields.Boolean(string='Update Stage',
                                     help="For updating the stage")
    stage_id = fields.Many2one('project.project.stage', string='Stages',
                               help="getting stages", required=True)

    def mass_update_project_stage(self):
        """ Update project stage pf multiple stage at a time"""
        for project in self.env['project.project'].browse(
                self._context['active_ids']):
            project.update({
                'project_stage_id': self.stage_id.id
            })
