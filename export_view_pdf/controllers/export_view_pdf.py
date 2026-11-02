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


class ExportDataController(http.Controller):
    """Controller to fetch selected field data and export it to PDF."""
    @http.route('/get_data', auth="user", type='jsonrpc')
    def action_get_export_data(self, **kw):
        """Method to fetch required export details and format them for PDF."""
        model = kw.get('model')
        if not model or model not in request.env:
            return {'data': [], 'header': []}

        model_obj = request.env[model]
        model_obj.check_access('read')

        fields = kw.get('fields') or []
        field_names = [f['name'] for f in fields if isinstance(f, dict) and f.get('name') in model_obj._fields]
        columns_headers = [
            val.get('label', val.get('name', '')).strip()
            for val in fields
            if isinstance(val, dict) and val.get('name') in model_obj._fields
        ]

        res_ids = kw.get('res_ids') or []
        domain = [('id', 'in', res_ids)] if res_ids else (kw.get('domain') or [])
        groupby = kw.get('grouped_by') or []

        records = (
            model_obj.browse(res_ids).exists()
            if res_ids
            else model_obj.search(domain, offset=0, limit=False, order=False)
        )

        if groupby:
            group_field = groupby[0].split(':')[0]
            groupby_type = [
                model_obj._fields[x.split(':')[0]].type
                for x in groupby
                if x.split(':')[0] in model_obj._fields
            ]
            filter_domain = kw.get('domain') or []
            group_by = []
            export_data = []
            if group_field in model_obj._fields:
                groups = model_obj._read_group(
                    filter_domain,
                    groupby=[group_field],
                    aggregates=['__count'],
                )
                for group_val, count in groups:
                    if group_val:
                        if hasattr(group_val, '_name'):
                            group_domain = [(group_field, '=', group_val.id)]
                            val_display = (group_val.id, group_val.display_name)
                        else:
                            group_domain = [(group_field, '=', group_val)]
                            val_display = group_val
                    else:
                        group_domain = [(group_field, '=', False)]
                        val_display = False

                    sub_records = model_obj.search(filter_domain + group_domain)
                    group_export = (
                        sub_records.export_data(field_names).get('datas', [])
                        if field_names
                        else []
                    )
                    group_tuple = (
                        {'count': count},
                        val_display,
                        [group_export],
                        [],
                    )
                    group_by.append(group_tuple)

            return {
                'header': columns_headers,
                'data': export_data,
                'type': groupby_type,
                'other': group_by,
            }

        export_data = records.export_data(field_names).get('datas', []) if field_names else []
        return {
            'data': export_data,
            'header': columns_headers,
        }

