# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ajith V (odoo@cybrosys.com)
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
################################################################################
import json
from odoo import http
from odoo.http import content_disposition, request, serialize_exception as \
    _serialize_exception
from odoo.tools import html_escape


class SurveyXlsReportController(http.Controller):
    """This is used for get the xlsx report"""

    @http.route('/xlsx_reports', type='http', auth='user',
                methods=['POST'], csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_name):
        """
        Generate and return an XLSX report for the specified model.

        This method handles the HTTP POST request to generate an XLSX report based on the provided model and options.
        The report is generated using the custom `get_xlsx_report` method of the specified model and returned as an HTTP response.

        Args:
            model (str): The name of the model for which the report is to be generated.
            options (str): A JSON string containing the options for generating the report.
                           It is parsed into a Python dictionary before being passed to the report generation method.
            output_format (str): The format of the output report.
                                 This method currently only supports 'xlsx'.
            report_name (str): The desired name of the generated report file.

        Returns:
            Response: An HTTP response containing the generated XLSX report.
                      If an error occurs during the report generation, an error response is returned with the exception details.

        Raises:
            Exception: If there is any issue during the report generation, it is caught and returned as a JSON response with an error message.

        Note:
            - This route is accessible to authenticated users only.
            - CSRF protection is disabled for this route.
            - A dummy token is set in the response cookies to meet API expectations.
        """
        uid = request.session.uid
        report_obj = request.env[model].with_user(uid)
        options = json.loads(options)
        token = 'dummy-because-api-expects-one'
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
                report_obj.get_xlsx_report(options, response)
            response.set_cookie('fileToken', token)
            return response
        except Exception as e:
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': _serialize_exception(e)
            }
            return request.make_response(html_escape(json.dumps(error)))
