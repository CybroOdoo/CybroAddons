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
#############################################################################
import json

from werkzeug.exceptions import BadRequest

from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition

XLSX_REPORT_NAME = 'Project Report'
XLSX_CONTENT_TYPE = ('application/vnd.openxmlformats-officedocument.'
                     'spreadsheetml.sheet')


class XLSXReportController(http.Controller):
    """ Serves the project XLSX report as a file download. """

    @http.route('/project_report_pdf/xlsx_report', type='http', auth='user',
                methods=['POST'])
    def get_report_xlsx(self, options, output_format):
        """ Generates the project XLSX report for the given options. """
        if output_format != 'xlsx':
            raise BadRequest(request.env._(
                "Unsupported output format: %(format)s",
                format=output_format,
            ))
        try:
            options = json.loads(options)
        except ValueError as error:
            raise BadRequest(request.env._("Invalid report options.")) from error
        if not isinstance(options, dict):
            raise BadRequest(request.env._("Invalid report options."))
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', XLSX_CONTENT_TYPE),
                ('Content-Disposition',
                 content_disposition(f'{XLSX_REPORT_NAME}.xlsx')),
            ],
        )
        request.env['project.report'].get_xlsx_report(options, response)
        return response
