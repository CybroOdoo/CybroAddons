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
from odoo.http.dispatcher import serialize_exception as _serialize_exception
from odoo.http.stream import content_disposition, request
from odoo.tools import html_escape


class XLSXReportController(http.Controller):
    """XLSX report streaming controller."""

    ALLOWED_MODELS = {
        'stock.product.report',
        'stock.valuation.report',
        'stock.move.report',
        'stock.transfer.report',
    }

    @http.route('/xlsx_reports', type='http', auth='user', methods=['POST'], csrf=True)
    def get_report_xlsx(self, model, options, output_format, **_kw):
        """Generate an XLSX report based on provided options and stream binary."""
        if model not in self.ALLOWED_MODELS or model not in request.env:
            return request.not_found()
        uid = request.session.uid
        report_obj = request.env[model].with_user(uid)
        if not hasattr(report_obj, 'get_xlsx_report'):
            return request.not_found()
        parsed_options = json.loads(options)
        token = 'dummy-because-api-expects-one'
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        (
                            'Content-Disposition',
                            content_disposition('Excel Report.xlsx'),
                        ),
                    ],
                )
                report_obj.get_xlsx_report(parsed_options, response)
                response.set_cookie('fileToken', token)
                return response
            return request.not_found()
        except Exception as e:  # pylint: disable=broad-exception-caught
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se,
            }
            return request.make_response(html_escape(json.dumps(error)))
