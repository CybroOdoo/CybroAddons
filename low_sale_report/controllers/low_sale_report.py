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
#    This program is distributed in the hope it will be useful,
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
import logging
from werkzeug.exceptions import Forbidden
from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition
from odoo.tools import html_escape

_logger = logging.getLogger(__name__)

ALLOWED_MODELS = {'low.sale.report'}


class XLSXReportController(http.Controller):
    """Controller route for generating and serving low sale XLSX reports."""

    @http.route(
        '/sale_low_xlsx_reports',
        type='http',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def get_report_xlsx(self, model, options, output_format, report_name):
        """Generate and serve an XLSX report file."""
        if model not in ALLOWED_MODELS or model not in request.env:
            raise Forbidden("Unauthorized model access.")
        uid = request.session.uid
        report_obj = request.env[model].with_user(uid)
        report_obj.check_access('read')
        options_data = json.loads(options)
        token = 'dummy-because-api-expects-one'
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition(f"{report_name}.xlsx")),
                    ],
                )
                report_obj.get_low_sale_xlsx_report(options_data, response)
            response.set_cookie('fileToken', token)
            return response
        except Exception as e:
            _logger.exception("Error while generating XLSX low sale report: %s", e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': str(e),
            }
            return request.make_response(html_escape(json.dumps(error)))
