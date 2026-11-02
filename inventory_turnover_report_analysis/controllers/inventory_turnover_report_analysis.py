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
import traceback

from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition
from odoo.tools import exception_to_unicode, html_escape


class XLSXReportController(http.Controller):
    """The JS file calls the URL '/xlsx_reports' to download the report."""
    @http.route('/xlsx_reports', type='http', auth='user', methods=['POST'],
                csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_name, **kw):
        """Controller function to generate the XLSX report."""
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
                'data': {
                    'name': f"{type(e).__module__}.{type(e).__name__}",
                    'debug': traceback.format_exc(),
                    'message': exception_to_unicode(e),
                    'arguments': [str(arg) for arg in e.args],
                },
            }
        return request.make_response(html_escape(json.dumps(error)))
