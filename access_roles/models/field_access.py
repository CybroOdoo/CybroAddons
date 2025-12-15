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


class FieldAccess(models.Model):
    """Manages access control for fields, buttons, tabs, and models."""
    _name = 'field.access'

    model_id = fields.Many2one('ir.model', domain="[('model', '!=', 'access.role')]")
    button_invisible = fields.Char(help='Field for setting button visibility')
    is_field_readonly = fields.Boolean(string='Readonly')
    is_field_invisible = fields.Boolean(string='Invisible')
    is_field_required = fields.Boolean(string='Required')
    is_remove_link = fields.Boolean(string='Remove External link')
    is_model_readonly = fields.Boolean(string='Readonly')
    is_hide_create = fields.Boolean(string='Hide Create')
    is_hide_delete = fields.Boolean(string='Hide Delete')
    is_hide_duplicate = fields.Boolean(string='Hide Duplicate')
    is_hide_archive = fields.Boolean(string='Hide Archive/UnArchive')
    is_hide_export = fields.Boolean(string='Hide Export')
    button_access_id = fields.Many2one('role.management')
    button_ids = fields.Many2many(
        'button.registry',
        string='Model Button',
        domain="[('model_id', '=', model_id)]")
    tab_ids = fields.Many2many('tab.registry', string='Tab',
                             domain="[('model_id', '=', model_id)]")
    access_field_id = fields.Many2one('role.management')
    fields_ids = fields.Many2many('ir.model.fields',
                                  domain="[('model_id', '=', model_id)]")
    access_model_id = fields.Many2one('role.management')
    hide_report_ids = fields.Many2many('ir.actions.report',
                                     domain="[('model_id', '=', model_id)]")
    hide_actions_ids = fields.Many2many('ir.actions.server',
                                      domain="[('model_id', '=', model_id)]")
    filter_access_id = fields.Many2one('role.management')
    filter_ids = fields.Many2many('filter.registry', string='Filters',
                                domain="[('model_id', '=', model_id)]")
    group_ids = fields.Many2many('groupby.registry', string='GroupBy',
                               domain="[('model_id', '=', model_id)]")
    domain_access_id = fields.Many2one('role.management')
    domain_id = fields.Many2one('domain.model')

    @api.onchange('model_id')
    def _onchange_model_id(self):
        """Clears related fields when the model is changed."""
        self.fields_ids = False
        self.filter_ids = False
        self.group_ids = False
        self.button_ids = False
        self.hide_report_ids = False
        self.hide_actions_ids = False
        self.tab_ids = False
