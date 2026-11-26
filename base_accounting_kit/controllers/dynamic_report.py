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

from werkzeug.urls import url_parse

from odoo.http import request, route
from odoo.http.stream import content_disposition

from odoo.addons.web.controllers.report import ReportController

DYNAMIC_PDF = '/report/pdf/base_accounting_kit.dynamic_report_pdf'


class DynamicReportDownload(ReportController):
    """The PDF of the dynamic reports is named after the report and its
    period. Core names a PDF printed from options (no records) after the
    report action, which is shared by all dynamic reports."""

    @route()
    def report_download(self, data, context=None, token=None, readonly=True):
        response = super().report_download(data, context=context, token=token,
                                           readonly=readonly)
        url = json.loads(data)[0]
        if not url.startswith(DYNAMIC_PDF + '?'):
            return response
        query = url_parse(url).decode_query(cls=dict)
        payload = json.loads(query.get('options') or '{}')
        model = payload.get('model')
        if model not in request.env or not getattr(
                request.env[model], '_dynamic_report', False):
            return response
        ctx = {**json.loads(context or '{}'),
               **json.loads(query.get('context') or '{}')}
        report = request.env[model]
        if ctx.get('allowed_company_ids'):
            report = report.with_context(
                allowed_company_ids=ctx['allowed_company_ids'])
        filename = report._export_filename(payload.get('options') or {})
        response.headers['Content-Disposition'] = content_disposition(
            filename + '.pdf')
        return response
