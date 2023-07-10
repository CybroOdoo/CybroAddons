# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
from odoo import http
from odoo.http import request


class ExportData(http.Controller):
    """Controller class for fetching required details and exporting data."""
    @http.route('/get_data', auth="user", type='json')
    def get_export_data(self, **kw):
        """
        controller to fetch required details
        """
        field = kw['field']
        model = kw['model']
        mod = request.env[model]
        res_ids = kw['res_ids']
        field_label = kw['exported_fields']
        columns_headers = [val['label'].strip() for val in field_label]
        records = request.env[model].browse(res_ids)
        new_export_data = []
        if kw['grouped_by']:
            field_names = [field for field in kw['field']]
            groupby_type = [mod._fields[field.split(':')[0]].type for field in
                            kw['grouped_by']]
            domain = kw['domain']
            groups_data = mod.sudo().read_group(domain, field_names,
                                                kw['grouped_by'], lazy=False)
            group_by = []
            for rec in groups_data:
                ids = mod.search(rec['__domain'])
                list_key = [key for key in rec.keys() if
                            key in kw['field'] and key not in kw['grouped_by']]
                new_export_data = [ids.export_data(field).get('datas', [])]
                group_tuple = (
                    {'count': rec['__count']}, rec.get(kw['grouped_by'][0]),
                    new_export_data,
                    [(rec[key], field.index(key)) for key in list_key])
                group_by.append(group_tuple)
            return {'header': columns_headers, 'data': new_export_data,
                    'type': groupby_type, 'other': group_by}
        else:
            new_export_data = records.export_data(field).get('datas', [])
            return {'data': new_export_data, 'header': columns_headers}
