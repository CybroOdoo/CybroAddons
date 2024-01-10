# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohamed Muzammil VP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import json
from odoo import http
from odoo.http import content_disposition, request
from odoo.tools import html_escape


class PurchaseReportController(http.Controller):
    """Controller to generate excel report"""
    @http.route('/purchase_dynamic_xlsx_reports', type='http', auth='user',
                methods=['POST'], csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_data,
                        report_name, dfr_data):
        """ Method to generate and return an Excel report."""
        token = 'dummy-because-api-expects-one'
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition(
                            report_name + '.xlsx'))
                    ]
                )
                request.env[model].with_user(
                    request.session.uid).get_purchase_xlsx_report(
                    options, response, report_data, dfr_data)
            response.set_cookie('fileToken', token)
            return response
        except Exception:
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': 0,
            }
            return request.make_response(html_escape(json.dumps(error)))
