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
from odoo import _, http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.http.stream import content_disposition
from odoo.tools import html_escape


class TBXLSXReportController(http.Controller):
    """ This endpoint generates and provides an XLSX report in response to an
    HTTP POST request. The function uses the provided data to create the
    report and returns it as an XLSX file. """
    @http.route('/purchase_dynamic_xlsx_reports', type='http', auth='user',
                methods=['POST'])
    def get_report_xlsx(self, model, options, output_format, report_data,
                        report_name, dfr_data, **kw):
        """ Endpoint for getting xlsx report """
        uid = request.session.uid
        if model != 'dynamic.purchase.report':
            raise AccessError(_("Invalid report model."))
        request.env['purchase.order'].with_user(uid).check_access('read')
        report_obj = request.env[model].with_user(uid)
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
                report_obj.get_purchase_xlsx_report(options, response,
                                                    report_data, dfr_data)
            return response
        except Exception:
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': None
            }
            return request.make_response(html_escape(json.dumps(error)))
