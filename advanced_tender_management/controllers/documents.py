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
import mimetypes

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition


class CustomFileDownloadController(http.Controller):
    """Download of the documents published with a tender."""

    @http.route('/download/file/<int:file_id>', type='http', auth='public')
    def download_file(self, file_id, **_kwargs):
        """Download a document of a tender that is open to vendors."""
        record = request.env['tender.document'].sudo().browse(file_id).exists()
        if (not record or not record.attachment
                or record.tender_id.tender_state in ('draft', 'cancel')):
            raise NotFound()
        filename = record.filename or record.name or 'document'
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        return request.make_response(record.attachment.content, headers=[
            ('Content-Type', mime_type),
            ('Content-Disposition', content_disposition(filename)),
        ])
