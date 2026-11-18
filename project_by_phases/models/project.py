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
from odoo import models


class ProjectProject(models.Model):
    """Inherit 'project.project' and define action to open related
    project phases."""
    _inherit = 'project.project'

    def get_project_phases(self):
        """Return action to open project phases related to the project."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Phases',
            'view_mode': 'kanban,list,form',
            'res_model': 'project.phase',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

