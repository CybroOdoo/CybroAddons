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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition

# Largest file the preview accepts, in bytes.
MAX_PDF_SIZE = 20 * 1024 * 1024


class WebsitePDFPreviewController(http.Controller):
    """Preview a PDF chosen in the PDF Preview snippet."""

    @http.route('/file/uploaded/', type='http', auth='public', website=True,
                methods=['POST'], csrf=False, sitemap=False)
    def upload_files(self, attachment=None, **kwargs):
        """Send the uploaded PDF back so the browser displays it.

        Nothing is stored: the route has no side effect, so it needs no
        CSRF token (the snippet form is static HTML saved in the page).
        """
        if not getattr(attachment, 'filename', None):
            return self._upload_error(request.env._("Please choose a PDF file."))
        if not attachment.filename.lower().endswith('.pdf'):
            return self._upload_error(request.env._("Only PDF files are allowed."))
        content = attachment.read(MAX_PDF_SIZE + 1)
        if len(content) > MAX_PDF_SIZE:
            return self._upload_error(request.env._(
                "The file is too large. The maximum size is %(size)s MB.",
                size=MAX_PDF_SIZE // (1024 * 1024)))
        if not content.startswith(b'%PDF-'):
            return self._upload_error(request.env._("The file is not a valid PDF document."))
        return request.make_response(content, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(content)),
            ('Content-Disposition', content_disposition(attachment.filename, 'inline')),
            ('X-Content-Type-Options', 'nosniff'),
        ])

    @staticmethod
    def _upload_error(message):
        """Website page with the error message, answered with HTTP 400."""
        return request.render('website_pdf_preview_snippet.upload_error_template',
                              {'error_message': message}, status=400)
