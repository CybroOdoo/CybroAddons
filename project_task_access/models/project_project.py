# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ProjectProject(models.Model):
    """ To customise the access for the project and tasks """
    _inherit = "project.project"

    project_access_user_ids = fields.Many2many('res.users',
                                               string='Access Limited Users',
                                               help="The users who has "
                                               "access for this record")
    user_admin_check = fields.Boolean(string='sale_line_id_check',
                                      compute='_compute_user_admin_check',
                                      help="To check if the user is an Internal"
                                      " user or not")

    def _compute_user_admin_check(self):
        """ Determines if the current user is an admin to allow the
        'task_access_user_ids' field to be editable only by 'user_admin'."""
        for rec in self:
            if rec.env.user.id == rec.env.ref('base.user_admin').id:
                rec.user_admin_check = True
            else:
                rec.user_admin_check = False
