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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectTaskType(models.Model):
    """Inherits the project Task Type Model for adding new fields
    and functions"""
    _inherit = 'project.task.type'

    progress_bar = fields.Float(string='Progress (%)',
                                help='Set your progress of the stage')
    is_progress_stage = fields.Boolean(string='Is Progress Bar',
                                       help='You can only see the progress '
                                            'if you enable this')

    @api.constrains('progress_bar', 'sequence', 'is_progress_stage', 'project_ids')
    def project_progress_bar(self):
        """The Constraints for the project Task Type Model"""
        for rec in self:
            if not rec.is_progress_stage:
                continue
            if rec.progress_bar < 0.0 or rec.progress_bar > 100.0:
                raise UserError(_('The progress must be less than or equal to 100 and greater than or equal to 0.'))

            domain = [
                ('is_progress_stage', '=', True),
                ('id', '!=', rec.id),
            ]
            if rec.project_ids:
                domain.append(('project_ids', 'in', rec.project_ids.ids))
            else:
                domain.append(('project_ids', '=', False))

            other_stages = self.search(domain)
            for other in other_stages:
                if rec.progress_bar == other.progress_bar:
                    raise UserError(_('Ensure that the progress is not duplicated.'))
                if rec.progress_bar < other.progress_bar:
                    if float(rec.sequence) >= float(other.sequence):
                        raise UserError(
                            _('The progress in this stage must be greater than that of the '
                              'other stages progress bars. Alternatively, reassess '
                              'the priority assigned to this stage.'))
                else:
                    if float(rec.sequence) <= float(other.sequence):
                        raise UserError(
                            _('The progress in this stage must be less than that of the '
                              'other stages progress bars. Alternatively, reassess '
                              'the priority assigned to this stage.'))
