# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json
import logging

from werkzeug.exceptions import (BadRequest, Forbidden, InternalServerError,
                                 NotFound)

from odoo import http
from odoo.http import request
from odoo.http.dispatcher import serialize_exception
from odoo.http.stream import content_disposition
from odoo.tools import html_escape

_logger = logging.getLogger(__name__)

XLSX_CONTENT_TYPE = ('application/vnd.openxmlformats-officedocument.'
                     'spreadsheetml.sheet')


class XLSXReportController(http.Controller):
    """ Controller for xlsx report """

    @http.route('/xlsx_report', type='http', auth='user', methods=['POST'])
    def get_report_xlsx(self, model, options, output_format, report_name,
                        report_action=None, **kwargs):
        """Stream the xlsx workbook of a report.

        Only models that opt in with ``_xlsx_report_allowed = True`` are
        accepted, and the request runs with the user's own access rights.
        The CSRF token is sent by ``@web/core/network/download``.
        """
        if model not in request.env:
            raise NotFound()
        report_obj = request.env[model]
        if not getattr(report_obj, '_xlsx_report_allowed', False):
            raise Forbidden()
        if output_format == 'csv':
            # CSV only from reports that offer it (dynamic reports)
            if not hasattr(report_obj, 'get_csv_report'):
                raise BadRequest()
        elif output_format != 'xlsx':
            raise BadRequest()
        report_obj.check_access('read')
        try:
            csv = output_format == 'csv'
            response = request.make_response(
                None, headers=[
                    ('Content-Type', 'text/csv; charset=utf-8' if csv
                     else XLSX_CONTENT_TYPE),
                    ('Content-Disposition', content_disposition(
                        report_name + ('.csv' if csv else '.xlsx')))])
            if csv:
                report_obj.get_csv_report(json.loads(options), response)
            else:
                report_obj.get_xlsx_report(json.loads(options), response)
            return response
        except Exception as exc:
            _logger.warning("Error while generating the xlsx report %s",
                            report_name, exc_info=True)
            error = {
                'code': 0,
                'message': 'Odoo Server Error',
                'data': serialize_exception(exc),
            }
            res = request.make_response(html_escape(json.dumps(error)))
            raise InternalServerError(response=res) from exc
