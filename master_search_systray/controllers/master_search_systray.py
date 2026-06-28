# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fansa Jabeen A (odoo@cybrosys.com)
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
        if query != '':
            config_settings = request.env['ir.config_parameter'].sudo().get_param(
                'master_search_systray.master_search_installed_ids')
            if config_settings:
                config_settings_str = literal_eval(config_settings)
                config_settings_ids = [int(id_str) for id_str in config_settings_str]
                config_modules = request.env['ir.module.module'].sudo().search([
                    ('id', 'in', config_settings_ids)])
                module_names = [module.name for module in config_modules]
                modules = request.env['ir.module.module'].sudo().search([
                    ('name', 'in', module_names)])
                for module in modules:
                    models = request.env['ir.model'].sudo().search([])
                    filtered_models = models.filtered(
                        lambda m: module.name in m.modules)
                    for rec in filtered_models:
                        fields = rec.field_id.filtered(lambda f: f.store).mapped('name')
                        if rec._rec_name in fields:
                            temp_data = []
                            try:
                                request.env.cr.execute(
                                    "SELECT * FROM %s WHERE name ILIKE '%s'" % (
                                        rec.model.replace('.', '_'), '%' + query + '%'))
                                records = request.env.cr.dictfetchall()
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
                                if records:
                                    data.append(temp_data)
                                request.env.cr.commit()
                            except psycopg2.Error:
                                request.env.cr.rollback()
                                try:
                                    records = request.env[rec.model].search(
                                        [('name', 'ilike', query)])
                                    temp_data = []
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
