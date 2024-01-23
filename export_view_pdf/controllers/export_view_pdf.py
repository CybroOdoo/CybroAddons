# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    """This controller will fetch the data of the fields selected in the
     dialog to the pdf report."""
    @http.route('/get_data', auth="user", type='json')
    def action_get_export_data(self, **kw):
        """
        method to fetch required details
        """
        fields = kw['fields']
        model = kw['model']
        Model = request.env[model]
        field_names = [f['name'] for f in fields]
        columns_headers = [val['label'].strip() for val in fields]
        domain = [('id', 'in', kw['res_ids'])] \
            if kw['res_ids'] else kw['domain']
        groupby = kw['grouped_by']
        records = Model.browse(kw['res_ids']) \
            if kw['res_ids'] \
            else Model.search(domain, offset=0, limit=False, order=False)
        if groupby:
            field_names = [f['name'] for f in fields]
            groupby_type = [Model._fields[x.split(':')[0]].type for x in
                            kw['grouped_by']]
            domain = kw['domain']
            groups_data = Model.read_group(domain,
                                           [x if x != '.id' else 'id' for x in
                                            field_names], groupby, lazy=False)
            group_by = []
            for rec in groups_data:
                ids = Model.search(rec['__domain'])
                list_key = [x for x in rec.keys() if
                            x in field_names and x not in kw['grouped_by']]
                export_data = [ids.export_data(field_names).get('datas', [])]
                group_tuple = (
                    {'count': rec['__count']}, rec.get(kw['grouped_by'][0]),
                    export_data,
                    [(rec[x], field_names.index(x)) for x in list_key])
                group_by.append(group_tuple)
            return {'header': columns_headers, 'data': export_data,
                    'type': groupby_type, 'other': group_by}
        else:
            export_data = records.export_data(field_names).get('datas', [])
            return {'data': export_data, 'header': columns_headers}
