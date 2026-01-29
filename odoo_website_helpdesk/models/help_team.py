# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
from odoo import fields, models


class HelpDeskTeam(models.Model):
    """
    This model represents a Helpdesk Team in the system.

    HelpDeskTeam includes information such as the team's name, team members,
    email, project they are currently in, and whether they have permission to
    create tasks from tickets.

    This class inherits the Odoo 'models.Model' class.
    """
    _name = 'help.team'
    _description = 'Helpdesk Team'

    name = fields.Char(string='Name', help="Name of the Helpdesk Team")
    member_ids = fields.Many2many('res.users',
                                  string='Members',
                                  help="Users who belong to that Helpdesk Team")
    email = fields.Char(string='Email', help="Email")
    project_id = fields.Many2one('project.project',
                                 string='Project',
                                 help="The Project they are currently in")
    create_task = fields.Boolean(string="Create Task",
                                 help="Enable for allowing team to "
                                      "create tasks from tickets")
