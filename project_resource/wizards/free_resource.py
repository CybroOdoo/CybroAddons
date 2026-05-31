# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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


class FreeResource(models.TransientModel):
    """Wizard to add the period to get the free resource"""
    _name = 'free.resource'
    _description = 'Free Resource'

    date_from = fields.Date(
        string="Start Date",
        help="Start date of period for receiving the Free Resource")
    date_to = fields.Date(
        string="End Date",
        help="End date of period for receiving the Free Resource")

    def get_free_resource(self):
        """Get the list of free resource at the given period"""
        if self.date_from and self.date_to:
            busy_resource_ids = self.env['project.task'].get_free_resource_ids(
                self.date_from, self.date_to, exclude_task_id=None)
            domain = [('id', 'not in', busy_resource_ids), ('share', '=', False)]
        else:
            domain = [('share', '=', False)]

        return {
            'name': 'Free Resources' if self.date_from and self.date_to else 'All Resources',
            'view_mode': 'list,form',
            'target': 'main',
            'res_model': 'res.users',
            'views': [
                (self.env.ref('project_resource.res_users_view_list').id, 'list'),
                (self.env.ref('project_resource.res_users_view_form').id, 'form')
            ],
            'type': 'ir.actions.act_window',
            'domain': domain,
        }
