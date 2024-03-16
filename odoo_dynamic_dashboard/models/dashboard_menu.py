# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class DashboardMenu(models.Model):
    """
    This is the class DashboardMenu which is the subclass of the class Model
    which is here used to create the model dashboard.menu.
    """
    _name = "dashboard.menu"
    _description = "Dashboard Menu"

    name = fields.Char(string="Name", help="Name of the dashboard")
    parent_id = fields.Many2one('ir.ui.menu', string="Menu",
                                help="Parent of the dashboard")
    group_ids = fields.Many2many('res.groups', string='Groups',
                                 related='parent_id.groups_id',
                                 help="User need to be at least in one "
                                      "of these groups to see the menu")
    client_action_id = fields.Many2one('ir.actions.client',
                                       string='Client Action',
                                       help="Client Action Related "
                                            "to the dashboard")
    menu_id = fields.Many2one('ir.ui.menu', string="Created Menu",
                              help="Created menu")

    @api.model
    def create(self, vals):
        """
        Summary:
            This is the create function of the model DashboardMenu which is
            triggered when creating a new record in this model.
        Args:
            vals:
                The values when the user creating a new record.
        Returns:
            res:
                Returns the created record at the end
        """
        values = {
            'name': vals['name'],
            'tag': 'owl.dynamic_dashboard',
        }
        action_id = self.env['ir.actions.client'].create(values)
        vals['client_action_id'] = action_id.id
        menu_id = self.env['ir.ui.menu'].create({
            'name': vals['name'],
            'parent_id': vals['parent_id'],
            'action': f'ir.actions.client,{action_id.id}'
        })
        res = super(DashboardMenu, self).create(vals)
        res.menu_id = menu_id.id
        return res

    def write(self, vals):
        """
        Summary:
            This is the write function of the model DashboardMenu which is
            triggered when changing any value in the corresponding record.
        Args:
            vals:
                The values when the user creating a editing an record.
        Returns:
            Returns the updated record at the end
        """
        if self.menu_id:
            self.menu_id.update(vals)
        return super(DashboardMenu, self).write(vals)

    def unlink(self):
        """
        Summary:
            This is the unlink function of the model DashboardMenu which is
            triggered when unlinking any record in this model.
        Returns:
            Returns the record delete.
        """
        self.menu_id.unlink()
        return super(DashboardMenu, self).unlink()
