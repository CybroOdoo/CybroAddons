# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
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
import psycopg2
from ast import literal_eval
from odoo import http
from odoo.http import request


class MasterSearch(http.Controller):
    """Controller for the master search functionality."""

    @http.route("/master/search", methods=["POST"], type="json",
                auth="user")
    def master_search(self, query):
        """
        Perform a master search across all models in the system based on the
        given query.

        This method performs a search across multiple models in the Odoo
        system using the provided query string. The search is conducted on
        all stored fields within the models associated with the installed
        modules configured in the system.
        """
        data = []
        # Check if the query is not empty
        if query != '':
            # Get all models in the system in the res.config.settings
            config_settings = request.env['ir.config_parameter'].sudo().get_param(
                'master_search_systray.master_search_installed_ids')
            if config_settings:
                config_settings_str = literal_eval(config_settings)
                # Convert to list of integers
                config_settings_ids = [int(id_str) for id_str in config_settings_str]
                # Fetch ir.module.module records for the selected module IDs
                config_modules = request.env['ir.module.module'].sudo().search([
                    ('id', 'in', config_settings_ids)])
                # Collect module names from master_search_values
                module_names = [module.name for module in config_modules]
                # Fetch ir.module.module records for the selected module names
                modules = request.env['ir.module.module'].sudo().search([
                    ('name', 'in', module_names)])
                for module in modules:
                    models = request.env['ir.model'].sudo().search([])
                    filtered_models = models.filtered(
                        lambda m: module.name in m.modules)
                    # Loop through each model to perform the search
                    for rec in filtered_models:
                        # Filter out fields that are not stored in the database
                        fields = rec.field_id.filtered(lambda f: f.store).mapped('name')
                        # Check if the model's main name field is in the stored fields
                        if rec._rec_name in fields:
                            # Temporary list to store results for the current model
                            temp_data = []
                            try:
                                # Execute a raw SQL query to search records in the current model
                                request.env.cr.execute(
                                    "SELECT * FROM %s WHERE name ILIKE '%s'" % (
                                        rec.model.replace('.', '_'), '%' + query + '%'))
                                # Fetch the results as a list of dictionaries
                                records = request.env.cr.dictfetchall()
                                # If there are matching records, process and append them to temp_data
                                if len(records) >= 1:
                                    temp_data.append({
                                        'title': rec.name,
                                        'name': None,
                                        'id': None,
                                        'isChild': False,
                                        'isParent': True,
                                        'model': rec.model
                                    })
                                    for val in records:
                                        temp_data.append({
                                            'title': None,
                                            'name': val['name'],
                                            'id': val['id'],
                                            'isChild': True,
                                            'isParent': False,
                                            'model': rec.model
                                        })
                                # Append temp_data to the main result data
                                if records:
                                    data.append(temp_data)
                                request.env.cr.commit()
                            except psycopg2.Error:
                                request.env.cr.rollback()
                                try:
                                    # If an exception occurs, attempt to perform a search using Odoo API
                                    records = request.env[rec.model].search(
                                        [('name', 'ilike', query)])
                                    temp_data = []
                                    # If there are matching records, process and append them to temp_data
                                    if records:
                                        temp_data.append({
                                            'title': rec.name,
                                            'name': None,
                                            'id': None,
                                            'isChild': False,
                                            'isParent': True,
                                            'model': rec.model
                                        })
                                        for val in records:
                                            temp_data.append({
                                                'title': None,
                                                'name': val['name'],
                                                'id': val['id'],
                                                'isChild': True,
                                                'isParent': False,
                                                'model': rec.model
                                            })
                                        data.append(temp_data)
                                    request.env.cr.commit()
                                except Exception as e:
                                    request.env.cr.rollback()
        return data
