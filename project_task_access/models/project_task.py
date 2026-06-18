# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields, models


class ProjectTask(models.Model):
    """ The Class ProjectTask for the model project_task which is to
    customise the access for the records. """
    _inherit = 'project.task'

    task_access_user_ids = fields.Many2many('res.users',
                                            string='Access Limited Users',
                                            help="The users who has access "
                                            "for this record")
    is_internal_user = fields.Boolean(string='sale_line_id_check',
                                      compute='_compute_is_internal_user',
                                      help="The Compute field to check if "
                                      "the user is an Internal user or not")

    def _compute_is_internal_user(self):
        """The function computes a boolean field to check if the current
        user is the admin for the purpose of making the
        'task_access_user_ids' field editable only for 'user_admin'"""
        for rec in self:
            if rec.env.user.id == rec.env.ref('base.user_admin').id:
                rec.is_internal_user = True
            else:
                rec.is_internal_user = False
