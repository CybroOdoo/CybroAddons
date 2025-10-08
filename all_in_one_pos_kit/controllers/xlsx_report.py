# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
###############################################################################
import json
from odoo import http
from odoo.http import content_disposition, request
from odoo.tools import html_escape


class TBXLSXReportController(http.Controller):
    """Controller class for generating and downloading XLSX reports."""

    @http.route('/pos_dynamic_xlsx_reports', type='http', auth='user',
                methods=['POST'], csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_data,
                        report_name, dfr_data):
        """ Generate and download an XLSX report.
            :param model: The model name for which the report is generated.
            :param options: Options/configuration for the report.
            :param output_format: The output format of the report (e.g.,'xlsx')
            :param report_data: Data required for generating the report.
            :param report_name: The name of the report.
            :param dfr_data: Additional data required for the report.
            :returns: The HTTP response containing the generated XLSX report"""
        report_obj = request.env[model].with_user(request.session.uid)
        try:
            if output_format == 'xlsx':
                response = request.make_response(None, headers=[
                    ('Content-Type', 'application/vnd.ms-excel'), (
                    'Content-Disposition',
                    content_disposition(report_name + '.xlsx'))])
                report_obj.get_pos_xlsx_report(options, response, report_data,
                                               dfr_data)
            response.set_cookie('fileToken', 'dummy-because-api-expects-one')
            return response
        except Exception as e:
            error = {'code': 200, 'message': 'Odoo Server Error',
                     'data': http.serialize_exception(e)}
            return request.make_response(html_escape(json.dumps(error)))
