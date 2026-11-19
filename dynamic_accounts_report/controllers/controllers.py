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
from werkzeug.exceptions import BadRequest, Forbidden
from odoo import http
from odoo.http import request
from odoo.http.dispatcher import serialize_exception
from odoo.http.stream import content_disposition
from odoo.tools import html_escape

ALLOWED_MODELS = {
    'account.general.ledger',
    'account.trial.balance',
    'cash.book.report',
    'bank.book.report',
    'dynamic.balance.sheet.report',
    'account.partner.ledger',
    'age.payable.report',
    'age.receivable.report',
    'tax.report',
}


class XLSXReportController(http.Controller):
    @http.route(
        '/dynamic_account/xlsx_report',
        type='http',
        auth='user',
        methods=['POST'],
    )
    def get_report_xlsx(
        self, model, data, output_format, report_name, report_action,
        options=None
    ):
        """Generate an XLSX report based on the provided data and return it as
        a response.
            Args:
                model (str): The name of the model on which the report is based.
                data (str): The data required for generating the report.
                output_format (str): Desired output format (e.g., 'xlsx').
                report_name (str): Name of the generated report file.
                report_action (str): The XML ID of the calling action.
                options (dict, optional): Additional filter options.
            Returns:
                Response: The generated report file response.
        """
        if model not in ALLOWED_MODELS:
            raise Forbidden("Unauthorized model access")

        report_obj = request.env[model]
        token = 'dummy-because-api-expects-one'
        try:
            if output_format != 'xlsx':
                raise BadRequest(
                    f"Unsupported output format: {output_format}"
                )
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type',
                     'application/vnd.openxmlformats-'
                     'officedocument.spreadsheetml.sheet'),
                    ('Content-Disposition',
                     content_disposition(report_name + '.xlsx'))
                ]
            )
            report_obj.get_xlsx_report(
                data, response, report_name, report_action
            )
            response.set_cookie('fileToken', token)
            return response
        except Exception as e:
            se = serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
