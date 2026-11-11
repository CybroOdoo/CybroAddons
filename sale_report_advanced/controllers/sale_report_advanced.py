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
from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition

XLSX_MIMETYPE = (
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
REPORT_MODELS = (
    'sale.report.advance',
    'sale.report.analysis',
    'sale.report.category',
    'sale.report.indent',
    'sale.report.invoice',
    'sale.report.weekly',
)


class XLSXReportController(http.Controller):
    """Download the XLSX reports of the sale report wizards."""

    @http.route('/xlsx_reports', type='http', auth='user', methods=['POST'])
    def get_report_xlsx(self, model, options, report_name, **kwargs):
        """Generate an XLSX report and return it as a download.

        :param str model: wizard model of the report
        :param str options: JSON data of the report
        :param str report_name: name of the downloaded file
        :return: the XLSX file
        """
        if model not in REPORT_MODELS:
            raise request.not_found()
        response = request.make_response(None, headers=[
            ('Content-Type', XLSX_MIMETYPE),
            ('Content-Disposition', content_disposition(f'{report_name}.xlsx')),
        ])
        request.env[model].get_xlsx_report(options, response)
        return response
