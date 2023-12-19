# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class FreeResource(models.TransientModel):
    """Wizard to add the period to get the free resource"""
    _name = 'free.resource'

    date_from = fields.Date(string="Start Date", help="Start date")
    date_to = fields.Date(string="End Date", help="End date")

    def get_free_resource(self):
        """Get the list of free resource at the given period """
        date_from = self.date_from
        date_to = self.date_to
        if date_from and date_to:
            case = 'in'
            resource_ids = self.env['project.task'].\
                get_free_resource_ids(date_from, date_to)
        else:
            resource_ids = []
            case = 'not in'
        return {
            'name': 'Free Resource',
            'view_mode': 'tree,form',
            'target': 'main',
            'res_model': 'res.users',
            'views': [
              (self.env.ref('project_resource.res_users_view_tree').id, 'tree'),
              (self.env.ref('project_resource.res_users_view_form').id, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [('id', case, resource_ids), ('share', '=', False)],
             }
