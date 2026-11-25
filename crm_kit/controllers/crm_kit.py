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
import logging
from odoo import http, _
from odoo.http import request
from odoo.http.stream import content_disposition
from odoo.tools import html_escape

_logger = logging.getLogger(__name__)


class XLSXReportController(http.Controller):
    """Controller for generating and downloading XLSX reports."""

    @http.route('/xlsx_reports', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_name, **kw):
        """
        Generate an XLSX report based on the provided data and return it as a response.
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
                        ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                        ('Content-Disposition', content_disposition(report_name + '.xlsx'))
                    ]
                )
                report_obj.get_xlsx_report(options, response)
                response.set_cookie('fileToken', token)
                return response
            return request.make_response(
                html_escape(json.dumps({'code': 400, 'message': 'Invalid output format'})),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.exception("Error while generating XLSX report")
            error = {
                'code': 500,
                'message': _('Odoo Server Error: %s', str(e)),
            }
            return request.make_response(
                html_escape(json.dumps(error)),
                headers=[('Content-Type', 'application/json')]
            )
