# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Arjun S (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class DashboardMenu(models.Model):
    """Class to create new dashboard menu"""
    _name = "dashboard.menu"
    _description = "Dashboard Menu"

    name = fields.Char(string="Name",
                       help="Enter a name for the dashboard menu")
    menu_id = fields.Many2one('ir.ui.menu', string="Parent Menu",
                              help="Parent Menu Location of New Dashboard",
                              ondelete='cascade')
    group_ids = fields.Many2many('res.groups', string='Groups',
                                 related='menu_id.group_ids',
                                 help="User need to be at least in one of "
                                      "these groups to see the menu")
    client_action_id = fields.Many2one('ir.actions.client',
                                       string="Client Action",
                                       help="Client action of the "
                                            "corresponding dashboard menu")
    sequence = fields.Integer(name="Sequence",
                              help="Sequence to place the menu in the view",
                              default=5)
    related_menu_id = fields.Many2one('ir.ui.menu', string="Related Menu",
                                      help="Menu related to the dashboard menu")

    @api.model_create_multi
    def create(self, vals_list):
        """Create dashboard menus and link them properly with client actions."""
        actions = self.env['ir.actions.client']
        menus = self.env['ir.ui.menu']
        action_vals_list = [
            {'name': vals['name'], 'tag': 'OdooDynamicDashboard'} for vals in
            vals_list]
        actions = actions.create(action_vals_list)
        for vals, action in zip(vals_list, actions):
            vals['client_action_id'] = action.id
        dashboards = super().create(vals_list)
        for dashboard in dashboards:
            menu = menus.create({
                'name': dashboard.name,
                'parent_id': dashboard.menu_id.id,
                'sequence': dashboard.sequence,
                'is_from_dynamic_dashboard': True,
                'action': f'ir.actions.client,{dashboard.client_action_id.id}',
            })
            dashboard.related_menu_id = menu.id
        return dashboards

    def write(self, vals):
        """Efficiently update related dashboard menus and client actions."""
        res = super().write(vals)
        for rec in self:
            menu_rec = rec.related_menu_id
            if not menu_rec:
                continue
            name = vals.get('name', rec.name)
            parent_id = vals.get('menu_id', rec.menu_id.id)
            sequence = vals.get('sequence', rec.sequence)
            client_act_id = rec.client_action_id.id
            menu_rec.write({
                'name': name,
                'parent_id': parent_id,
                'sequence': sequence,
                'action': f'ir.actions.client,{client_act_id}',
            })
        return res

    def unlink(self):
        """Delete dashboard and its linked menu items safely."""
        blocks = self.env['dashboard.block'].search([
            ('client_action_id', 'in', self.mapped('client_action_id').ids)
        ])
        blocks.unlink()
        for item in self:
            item.related_menu_id.unlink()
        return super().unlink()
