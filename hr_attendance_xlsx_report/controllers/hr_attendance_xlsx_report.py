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
#############################################################################
import json
from odoo import http
from odoo.exceptions import AccessError
from odoo.http.stream import content_disposition, request
from odoo.http.dispatcher import serialize_exception
from odoo.tools import html_escape

ALLOWED_MODELS = {'employee.attendance.report'}


class XLSXReportController(http.Controller):
    """Xlsx Report controller."""

    @http.route('/xlsx_reports', type='http', auth='user', methods=['POST'])
    def get_report_xlsx(self, model, options, output_format, report_name):
        """Generate and stream the XLSX report."""
        if model not in ALLOWED_MODELS:
            raise AccessError("Unauthorized model for report generation.")
        report_obj = request.env[model].with_user(request.session.uid)
        report_obj.check_access('read')
        options = json.loads(options)
        token = 'dummy-because-api-expects-one'
        try:
            if output_format == 'xlsx':
                headers = [
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', content_disposition(
                        report_name + '.xlsx'
                    )),
                ]
                response = request.make_response(None, headers=headers)
                report_obj.get_xlsx_report(options, response)
                response.set_cookie('fileToken', token)
                return response
            return request.not_found()
        except Exception as e:
            se = serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
