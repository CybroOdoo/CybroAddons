# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
import base64
import mimetypes
from odoo import http
from odoo.http import request, Response


class CustomFileDownloadController(http.Controller):
    """Handles file download requests."""

    @http.route('/download/file/<int:file_id>', type='http', auth='public')
    def download_file(self, file_id, **_kwargs):
        """Downloads a file by its ID."""
        record = request.env['tender.document'].sudo().browse(file_id)
        if record and record.attachment:
            file_data = base64.b64decode(record.attachment)
            filename = record.filename
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
            return Response(
                file_data,
                mimetype=mime_type,
                headers={"Content-Disposition": f"attachment;filename={filename}"}
            )
        return request.not_found()
