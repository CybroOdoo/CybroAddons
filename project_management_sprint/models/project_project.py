# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
###############################################################################
from odoo import models


class ProjectProject(models.Model):
    """ Inheriting project_project model to add sprint features """
    _inherit = 'project.project'

    def action_get_sprint(self):
        """ Getting sprint inside the project """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sprints',
            'view_mode': 'tree,form',
            'res_model': 'project.sprint',
            'context': {'default_project_id': self.id},
            'domain': [('project_id', '=', self.id)],
        }
