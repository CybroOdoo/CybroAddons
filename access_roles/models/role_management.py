# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class RoleManagement(models.Model):
    """Manages access roles, permissions, and system restrictions for users."""
    _name = 'role.management'
    _description = 'Role Management'
    _inherit = ['mail.thread']

    name = fields.Char(required=True)
    domain_ids = fields.Many2many('domain.model')
    is_debug = fields.Boolean(
        string='Disable Debug Mode',
        help='Disable the option to enable debug mode for the user'
    )
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
        all_selected = self.search([('id', 'not in', self.ids)]).mapped('role_ids').ids
        for record in self:
            record.selected_role_ids = all_selected

    @api.depends('menu_ids')
    def _compute_access_role_menu_ids(self):
        """Compute access roles menu id to prevent the menu from hiding."""
        menu = self.env.ref('access_roles.access_role_menu_root', raise_if_not_found=False)
        menu_id = menu.id if menu else False
        for record in self:
            record.access_role_menu_ids = [fields.Command.link(menu_id)] if menu_id else []

    @api.model
    def get_role_restrictions(self):
        user = self.env.user
        role = user.access_role_id
        if not role:
            return {}
        rms = self.sudo().search([('role_ids', 'in', role.id)])
        if role.role_management_id:
            rms |= role.role_management_id.sudo()
        if rms:
            return {
                'is_debug': any(rms.mapped('is_debug')),
                'is_chatter': any(rms.mapped('is_chatter')),
            }
        return {}

    @api.model
    def get_export_restrictions(self, user_id=None):
        """Retrieve model-based restrictions for a user.
        This function is used to determine which export, archive, reports,
        and actions should be hidden for the user based on their assigned
        access role. The data is passed to the JavaScript file for frontend
        enforcement.
        :param int user_id: The ID of the user for whom restrictions are being retrieved.
        :return: A list of dictionaries containing model-specific restrictions.
        :rtype: list of dict
        """
        user = self.env['res.users'].browse(user_id) if user_id else self.env.user
        role = user.access_role_id
        if not role:
            return []
        rms = self.sudo().search([('role_ids', 'in', role.id)])
        if role.role_management_id:
            rms |= role.role_management_id.sudo()
        if not rms:
            return []
        return rms.model_access_ids.mapped(
            lambda r: {"model": r.model_id.model, "is_hide_export": r.is_hide_export,
                       "is_hide_archive": r.is_hide_archive,
                       "report_id": r.hide_report_ids.ids,
                       "action_id": r.hide_actions_ids.ids}
        )

    @api.model
    def check_model_access_restrictions(self, user_id=None, model_name=None):
        """
        Check if create access and readonly mode are restricted for the user on a specific model.
        :param user_id: ID of the user to check
        :param model_name: Technical name of the model to check
        :return: Dictionary containing is_hide_create and is_model_readonly
        """
        user = self.env['res.users'].browse(user_id) if user_id else self.env.user
        role = user.access_role_id
        access_data = {}
        if not role:
            return access_data
        rms = self.sudo().search([('role_ids', 'in', role.id)])
        if role.role_management_id:
            rms |= role.role_management_id.sudo()
        if rms:
            model_access = rms.model_access_ids.filtered(
                lambda r: r.model_id.model == model_name
            )
            if model_access:
                access_data['is_hide_create'] = any(model_access.mapped('is_hide_create'))
                access_data['is_model_readonly'] = any(
                    model_access.mapped('is_model_readonly'))
        return access_data

    def write(self, vals):
        """Override write to maintain role_management_id on linked roles and clear caches."""
        res = super().write(vals)
        if 'role_ids' in vals:
            for record in self:
                for role in record.role_ids:
                    if role.role_management_id != record:
                        role.role_management_id = record.id
        self.env.invalidate_all()
        self.env.transaction.invalidate_ormcache()
        self.env.transaction.invalidate_ormcache('templates')
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically link roles with role management records and clear caches."""
        records = super(RoleManagement, self).create(vals_list)
        for record in records:
            for role in record.role_ids:
                if not role.role_management_id:
                    role.write({'role_management_id': record.id})
        self.env.invalidate_all()
        self.env.transaction.invalidate_ormcache()
        self.env.transaction.invalidate_ormcache('templates')
        return records

    def unlink(self):
        """Override unlink to clear menu caches."""
        res = super().unlink()
        self.env.invalidate_all()
        self.env.transaction.invalidate_ormcache()
        self.env.transaction.invalidate_ormcache('templates')
        return res

    def action_open_domain_form(self):
        """Opens the domain form when clicking on domain_id"""
        self.ensure_one()
        domain_id = self.domain_access_ids.domain_id[:1].id if self.domain_access_ids else False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Domain Configuration',
            'res_model': 'domain.model',
            'view_mode': 'form',
            'res_id': domain_id,
            'target': 'new',
        }
