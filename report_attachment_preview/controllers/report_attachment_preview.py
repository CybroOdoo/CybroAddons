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
from urllib.parse import quote

from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition
from odoo.tools.safe_eval import safe_eval, time

from odoo.addons.web.controllers.binary import Binary
from odoo.addons.web.controllers.report import ReportController


class ReportAttachmentPreviewBinary(Binary):
    """Serve binary content inline so the browser previews it in a new tab
    instead of downloading it."""

    @http.route()
    def content_common(self, **kwargs):
        """Turn ``attachment`` content dispositions into ``inline`` ones,
        keeping the file name, so PDF reports and attachments open in the
        browser even when requested with ``download=true``."""
        res = super().content_common(**kwargs)
        disposition = res.headers.get('Content-Disposition')
        if disposition and disposition.startswith('attachment'):
            res.headers['Content-Disposition'] = disposition.replace(
                'attachment', 'inline', 1)
        return res


class ReportAttachmentPreviewReport(ReportController):
    """Serve PDF reports from a URL ending with the report file name.

    Browser PDF viewers use the last URL segment as the tab title and as the
    default name when saving, so ``/report/pdf/<report>/65`` shows "65".
    """

    @http.route([
        '/report_attachment_preview/pdf/<reportname>',
        '/report_attachment_preview/pdf/<reportname>/<docids>',
    ], type='http', auth='user', readonly=True)
    # pylint: disable=unused-argument
    def report_preview(self, reportname, docids=None, **data):
        """Redirect to the preview URL ending with the report file name,
        keeping the query string (report options and context)."""
        filename = self._get_preview_filename(reportname, docids)
        path = '/'.join(
            part for part in ['/report_attachment_preview/view', reportname,
                              docids, quote(filename)] if part)
        query = request.httprequest.query_string.decode()
        return request.redirect(f'{path}?{query}' if query else path)

    @http.route([
        '/report_attachment_preview/view/<reportname>/<filename>',
        '/report_attachment_preview/view/<reportname>/<docids>/<filename>',
    ], type='http', auth='user', website=True, readonly=True)
    def report_preview_view(self, reportname, filename, docids=None, **data):
        """Render the PDF report inline under its file name."""
        response = self.report_routes(
            reportname, docids=docids, converter='pdf', **data)
        response.headers['Content-Disposition'] = content_disposition(
            filename, 'inline')
        return response

    def _get_preview_filename(self, reportname, docids):
        """Return the report file name, computed like ``report_download``:
        the evaluated ``print_report_name`` for a single record, otherwise
        the report name. Slashes are replaced so the name stays one URL
        segment."""
        report = request.env['ir.actions.report']._get_report_from_name(
            reportname)
        filename = report.name or reportname
        if docids and report.print_report_name:
            ids = [int(i) for i in docids.split(',') if i.isdigit()]
            records = request.env[report.model].browse(ids)
            if len(records) == 1:
                filename = safe_eval(report.print_report_name,
                                     {'object': records, 'time': time})
        return f"{filename}.pdf".replace('/', '_')
