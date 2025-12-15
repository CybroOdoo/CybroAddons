# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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


class RoleManagement(models.Model):
    """Manages access roles, permissions, and system restrictions for users."""
    _name = 'role.management'
    _description = 'Role Management'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True)
    domain_ids = fields.Many2many('domain.model')
    is_debug = fields.Boolean(
        string='Disable Debug Mode',
        help='Disable the option to enable debug mode for the user')
    is_chatter = fields.Boolean(
        string='Disable chatter',
        help='Disable chatter for the role'
    )
    is_readonly = fields.Boolean(
        string='Make System ReadOnly',
        help='Make system readonly'
    )
    role_ids = fields.Many2many('access.role', string='Roles',
                                domain="[('id','not in', selected_role_ids)]")
    menu_ids = fields.Many2many('ir.ui.menu', domain="[('id','not in', access_role_menu_ids)]")
    access_role_menu_ids = fields.Many2many('ir.ui.menu', compute='_compute_access_role_menu_ids')
    selected_role_ids = fields.Many2many('access.role',
                                         compute='_compute_selected_role_ids')
    field_access_ids = fields.One2many('field.access', 'access_field_id')
    model_access_ids = fields.One2many('field.access', 'access_model_id')
    button_access_ids = fields.One2many('field.access', 'button_access_id')
    domain_access_ids = fields.One2many('field.access', 'domain_access_id')
    filter_access_ids = fields.One2many('field.access', 'filter_access_id')

    @api.depends('role_ids')
    def _compute_selected_role_ids(self):
        """Compute selected roles to prevent duplicate role assignments."""
        for record in self:
            record.selected_role_ids = self.search([]).mapped('role_ids').ids
            for role in record.role_ids:
                role.role_management_id = record.id

    @api.depends('menu_ids')
    def _compute_access_role_menu_ids(self):
        """Compute access roles menu id to prevent the menu from hiding."""
        menu_id = self.env.ref('access_roles.access_role_menu_root').id
        self.access_role_menu_ids = [fields.Command.link(menu_id)]

    @api.model
    def get_role_restrictions(self, user_id):
        user = self.env.user
        role_management = user.access_role_id.role_management_id

        # Always return a dictionary
        if not role_management:
            return {
                "is_debug": False,
                "is_chatter": False,
                "is_readonly": False,
            }

        return {
            "is_debug": role_management.is_debug or False,
            "is_chatter": role_management.is_chatter or False,
            "is_readonly": role_management.is_readonly or False,
        }

    @api.model
    def get_export_restrictions(self, user_id):
        """Retrieve model-based restrictions for a user.
        This function is used to determine which export, archive, reports,
        and actions should be hidden for the user based on their assigned
        access role. The data is passed to the JavaScript file for frontend
        enforcement.
        :param int user_id: The ID of the user for whom restrictions are being retrieved.
        :return: A list of dictionaries containing model-specific restrictions.
        :rtype: list of dict
        """
        user = self.env.user
        if not user.access_role_id or not user.access_role_id.role_management_id:
            return []
        return user.access_role_id.role_management_id.model_access_ids.mapped(
            lambda r: {"model": r.model_id.model, "is_hide_export": r.is_hide_export,
                       "is_hide_archive": r.is_hide_archive,
                       "report_id": r.hide_report_ids.ids,
                       "action_id": r.hide_actions_ids.ids}
        )

    @api.model
    def check_model_access_restrictions(self, user_id, model_name):
        """
        Check if create access and readonly mode are restricted for the user on a specific model.
        :param user_id: ID of the user to check
        :param model_name: Technical name of the model to check
        :return: Dictionary containing is_hide_create and is_model_readonly
        """
        user = self.env.user
        role_management = user.access_role_id.role_management_id
        access_data = {}
        if role_management:
            model_access = role_management.model_access_ids.filtered(
                lambda r: r.model_id.model == model_name
            )
            if model_access:
                access_data['is_hide_create'] = any(model_access.mapped('is_hide_create'))
                access_data['is_model_readonly'] = any(
                    model_access.mapped('is_model_readonly'))
        return access_data

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically link roles with role management records."""
        records = super(RoleManagement, self).create(vals_list)
        for record in records:
            for role in record.role_ids:
                if not role.role_management_id:
                    role.write({'role_management_id': record.id})
        return records

    def action_open_domain_form(self):
        """Opens the domain form when clicking on domain_id"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Domain Configuration',
            'res_model': 'domain.model',
            'view_mode': 'form',
            'res_id': self.domain_access_ids.domain_id.id,
            'target': 'new'
        }
