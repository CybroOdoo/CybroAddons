"""Excel report"""
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
import json
import xml.etree.ElementTree as ET
from odoo import http
from odoo.http import content_disposition, request
from odoo.tools import html_escape


class XLSXReportController(http.Controller):
    """Excel report for one2many fields"""

    @http.route('/xlsx_reports', type='http', auth='user', methods=['POST'],
                csrf=False)
    def get_report_xlsx(self,
                        report_name='excel', **kwargs):
        """Used to get the report data that are fetched from the one2many"""
        model = kwargs.get('current_model')
        model_id = kwargs.get('id')
        field = kwargs.get('field')
        views = request.env['ir.ui.view'].search([('model', '=', model),
                                                  ('type', '=', 'tree')],
                                                 order='id asc', limit=1)
        tree = ET.fromstring(views.arch)
        names = [field.get('name') for field in tree.findall('field')]
        report_data = request.env[model].sudo().search_read(
            domain=[(field, '=', int(model_id))],
            fields=names)
        uid = request.session.uid
        report_obj = request.env['one2many.report.excel'].with_user(uid)
        output_format = 'xlsx'
        token = 'dummy-because-api-expects-one'
        # print(report_data[1]['order_id'])
        # print(report_data['order_id'])
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition',
                         content_disposition(report_name + '.xlsx'))
                    ]
                )
                report_obj.get_xlsx_report(report_data, names, response)
            response.set_cookie('fileToken', token)
            return response
        except Exception as e:
            se = http.serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
        return request.make_response(html_escape(json.dumps(error)))
