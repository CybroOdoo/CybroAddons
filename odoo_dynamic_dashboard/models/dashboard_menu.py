# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class DashboardMenu(models.Model):
    """Class to create new dashboard menu"""
    _name = "dashboard.menu"
    _description = "Dashboard Menu"

    name = fields.Char(string="Name", ondelete='cascade',
                       help="Enter a name for the dashboard menu")
    menu_id = fields.Many2one('ir.ui.menu', string="Parent Menu",
                              help="Parent Menu Location of New Dashboard",
                              ondelete='cascade')
    group_ids = fields.Many2many('res.groups', string='Groups',
                                 related='menu_id.groups_id',
                                 help="User need to be at least in one of "
                                      "these groups to see the menu")
    client_action_id = fields.Many2one('ir.actions.client',
                                       string="Client Action",
                                       help="Client action of the "
                                            "corresponding dashboard menu")

    @api.model
    def create(self, vals):
        """Function to create new dashboard menu"""
        action_id = self.env['ir.actions.client'].create([{
            'name': vals['name'],
            'tag': 'OdooDynamicDashboard',
        }])
        vals['client_action_id'] = action_id.id
        self.env['ir.ui.menu'].create([{
            'name': vals['name'],
            'parent_id': vals['menu_id'],
            'action': 'ir.actions.client,%d' % (action_id.id,)
        }])
        return super(DashboardMenu, self).create(vals)

    def write(self, vals):
        """Function to save edited data in dashboard menu"""
        for rec in self:
            client_act_id = rec['client_action_id'].id
            self.env['ir.ui.menu'].search(
                [('parent_id', '=', rec['menu_id'].id),
                 ('action', '=', f'ir.actions.client,{client_act_id}')]).write({
                'name': vals['name'] if 'name' in vals.keys() else rec['name'],
                'parent_id': vals['menu_id'] if 'menu_id' in vals.keys() else
                rec['menu_id'],
                'action': f'ir.actions.client,{client_act_id}'
            })
        return super(DashboardMenu, self).write(vals)

    def unlink(self):
        """Delete dashboard along with menu item"""
        for rec in self:
            self.env['ir.ui.menu'].search(
                [('parent_id', '=', rec['menu_id'].id),
                 ('action', '=',
                  f'ir.actions.client,{rec["client_action_id"].id}')]).unlink()
        return super(DashboardMenu, self).unlink()
