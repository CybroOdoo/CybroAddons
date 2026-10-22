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
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition
from odoo.tools import html_escape


class XLSXReportController(http.Controller):
    """ Controller for xlsx report """
    @http.route('/xlsx_report', type='http', auth='user', methods=['POST'],
                csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_name):
        """ Get xlsx report data """
        if model != 'res.partner':
            raise NotFound()
        report_obj = request.env[model]
        options = json.loads(options)
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None, headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition(
                            report_name + '.xlsx'))])
                report_obj.get_xlsx_report(options, response)
                return response
        except Exception as event:
            serialize = http.serialize_exception(event)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': serialize
            }
            return request.make_response(html_escape(json.dumps(error)))
