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
from odoo import http
from odoo.http import request


class ExportData(http.Controller):
    """ Controller class for exporting data from Odoo models."""

    def _get_export_rows(self, model, fields, res_ids=None, domain=None):
        """Return the column headers and the exported rows of the list.

        :param str model: Name of the Odoo model
        :param list fields: Fields to export, as dicts with ``name`` and
            ``label`` keys
        :param list res_ids: IDs of the selected records (optional)
        :param list domain: Domain of the list, used when no record is
            selected (optional)
        :return: tuple (headers, rows)"""
        records = request.env[model]
        if res_ids:
            records = records.browse(res_ids)
        else:
            records = records.search(domain or [])
        field_names = [field['name'] for field in fields]
        headers = [field['label'].strip() for field in fields]
        rows = records.export_data(field_names).get('datas', [])
        return headers, rows

    @http.route('/get_data', auth="user", type='jsonrpc')
    def get_export_data(self, model, fields, res_ids=None, domain=None,
                        **kwargs):
        """Return the data of the list to print it in PDF.

        :return: Dictionary containing exported data and column headers"""
        headers, rows = self._get_export_rows(model, fields, res_ids, domain)
        return {'data': rows, 'header': headers}

    @http.route('/get_data/copy', auth="user", type='jsonrpc')
    def get_export_data_copy(self, model, fields, res_ids=None, domain=None,
                             **kwargs):
        """Return the data of the list to copy it to the clipboard.

        :return: List of rows, starting with the column headers"""
        headers, rows = self._get_export_rows(model, fields, res_ids, domain)
        return [headers] + rows
