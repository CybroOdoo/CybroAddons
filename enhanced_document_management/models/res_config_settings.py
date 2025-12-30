# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj(<https://www.cybrosys.com>)
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
        help="set the time limit for the deleted files",
        config_parameter='enhanced_document_management.trash')

    @api.model_create_multi
    def create(self, vals_list):
        """Create method to set scheduled action's interval number for
         Google Drive and OneDrive synchronization.
        This method is used to create or update the interval number of
         scheduled actions for Google Drive and OneDrive
        synchronization based on the provided configuration values.
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
        """
            Set 'is_crm_install' field for all 'document.file' records.
            Args:
                vals_list (list): List of dictionaries containing values.
            Returns:
                None
        """
        records = self.env['document.file'].search([])
        is_crm_install = vals_list[0].get('module_crm')
        for record in records:
            record.write({'is_crm_install': is_crm_install})

    def is_project_installed(self, vals_list):
        """
            Set 'is_project_install' field for all 'document.file' records.
            Args:
                vals_list (list): List of dictionaries containing values.
            Returns:
                None
        """
        records = self.env['document.file'].search([])
        is_project_install = vals_list[0].get('module_project')
        for record in records:
            record.write({'is_project_install': is_project_install})
