# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu K P (odoo@cybrosys.com)
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
###############################################################################
import json
from odoo import http
from odoo.http import content_disposition, request
from odoo.tools import html_escape


class XLSXReportController(http.Controller):
    """Controller for XlsX report"""

    @http.route('/xlsx_reports', type='http', auth='user',
                methods=['POST'], csrf=False)
    def get_room_booking_report_xlsx(self, model, options, output_format,
                                     report_name):
        """Function for generating xlsx report"""
        report_obj = request.env[model].sudo()
        options = json.loads(options)
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[('Content-Type', 'application/vnd.ms-excel'),
                             ('Content-Disposition',
                              content_disposition(report_name + '.xlsx'))]
                )
                report_obj.get_xlsx_report(options, response)
                response.set_cookie('fileToken', 'dummy token')
                return response
        except Exception as e:
            s_error = http.serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': s_error
            }
            return request.make_response(html_escape(json.dumps(error)))
