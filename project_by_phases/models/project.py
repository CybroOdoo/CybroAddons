# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (Contact : odoo@cybrosys.com)
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
#############################################################################
from odoo import models


class ProjectProject(models.Model):
    """Inherits 'project.project' and define the action for open the related
    project phase model from project module.  """
    _inherit = 'project.project'

    def get_project_phases(self):
        """Function for open project phases related to the project in the
        kanban view."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Phases',
            'view_mode': 'kanban,list,form',
            'res_model': 'project.phase',
            'domain': [('project_id', '=', self.display_name)],
        }
