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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """ Inherited res.config.settings to add trash limit field"""
    _inherit = 'res.config.settings'

    trash = fields.Integer(
        string='Trash Limit',
        default=30,
        help="Set the time limit (in days) for retaining deleted files in the trash.",
        config_parameter='enhanced_document_management.trash')
    is_module_crm = fields.Boolean(
        string="CRM", compute='_compute_modules_installed')
    is_module_project = fields.Boolean(
        string="Project", compute='_compute_modules_installed')

    def _is_module_installed(self, module_name):
        """Return whether a technical module is installed."""
        module = self.env['ir.module.module'].sudo().search(
            [('name', '=', module_name)], limit=1)
        return module.state == 'installed'

    def _compute_modules_installed(self):
        """Compute the installation status of related modules."""
        is_crm_installed = self._is_module_installed('crm')
        is_project_installed = self._is_module_installed('project')
        for rec in self:
            rec.is_module_crm = is_crm_installed
            rec.is_module_project = is_project_installed

    @api.model_create_multi
    def create(self, vals_list):
        """Create method to update document file settings based on module
        installation status.
        Args:
            vals_list (list): List of dictionaries containing values to
             create the configuration settings.
        Returns:
            RecordSet: The created configuration settings record."""
        self.is_crm_installed(vals_list)
        self.is_project_installed(vals_list)
        res = super(ResConfigSettings, self).create(vals_list)
        return res

    def is_crm_installed(self, vals_list):
        """Set 'is_crm_install' field for all 'document.file' records."""
        crm_vals = [
            v.get('is_module_crm') for v in vals_list if 'is_module_crm' in v
        ]
        if crm_vals:
            is_crm_install = crm_vals[-1]
            self.env['document.file'].search([
                ('is_crm_install', '!=', is_crm_install)
            ]).write({'is_crm_install': is_crm_install})

    def is_project_installed(self, vals_list):
        """Set 'is_project_install' field for all 'document.file' records."""
        project_vals = [
            v.get('is_module_project')
            for v in vals_list
            if 'is_module_project' in v
        ]
        if project_vals:
            is_project_install = project_vals[-1]
            records = self.env['document.file'].search([
                ('is_project_install', '!=', is_project_install)
            ])
            if records:
                records.write({'is_project_install': is_project_install})
