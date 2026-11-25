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
import hashlib
import json
import os
import shutil
import unicodedata

from odoo import _, http, models
from odoo.exceptions import AccessError
from odoo.http import request


MAX_FILE_UPLOAD_SIZE = 2 * 1024 * 1024 * 1024 - 1  # 2 GB (PostgreSQL int4 limit)


class MediaAssetUploadController(http.Controller):
    """Direct multipart upload controller for media.asset's file field."""

    @http.route(
        '/media_repository/asset/upload_file',
        type='http',
        auth='user',
        methods=['POST'],
        max_content_length=MAX_FILE_UPLOAD_SIZE,
    )
    def upload_media_asset_file(self, model=None, res_id=None, **kwargs):
        """Handle direct multipart HTTP POST file upload for media assets.

        :param str model: Model name, expected to be 'media.asset'.
        :param int/str res_id: ID of the target media.asset record.
        :param dict kwargs: Additional request arguments.
        :return: Response containing JSON with uploaded file name or error details.
        :rtype: odoo.http.Response
        """
        model = model or kwargs.get('model')
        rec_id = res_id or kwargs.get('id') or kwargs.get('res_id')
        if model != 'media.asset':
            return request.make_response(
                json.dumps({'error': _("Invalid model.")}),
                [('Content-Type', 'application/json')],
                status=400,
            )

        try:
            asset = request.env['media.asset'].browse(int(rec_id))
            if not asset.exists():
                return request.make_response(
                    json.dumps({'error': _("Record does not exist.")}),
                    [('Content-Type', 'application/json')],
                    status=404,
                )
        except (ValueError, TypeError):
            return request.make_response(
                json.dumps({'error': _("Invalid record ID.")}),
                [('Content-Type', 'application/json')],
                status=400,
            )

        try:
            asset.check_access_rights('write')
            asset.check_access_rule('write')
        except AccessError:
            return request.make_response(
                json.dumps({'error': _("You are not allowed to upload a file on this record.")}),
                [('Content-Type', 'application/json')],
                status=403,
            )

        files = request.httprequest.files.getlist('ufile')
        if not files:
            return request.make_response(
                json.dumps({'error': _("No file uploaded.")}),
                [('Content-Type', 'application/json')],
                status=400,
            )
        uploaded_file = files[0]

        filename = uploaded_file.filename
        if request.httprequest.user_agent.browser == 'safari':
            filename = unicodedata.normalize('NFD', filename)

        # Stream file in 64KB chunks to calculate checksum and file size without buffering entire file in memory
        stream = uploaded_file.stream
        stream.seek(0)
        sha1 = hashlib.sha1()
        file_size = 0
        while True:
            chunk = stream.read(65536)
            if not chunk:
                break
            sha1.update(chunk)
            file_size += len(chunk)
        checksum = sha1.hexdigest()
        stream.seek(0)

        if file_size > MAX_FILE_UPLOAD_SIZE:
            return request.make_response(
                json.dumps({'error': _("File size exceeds the 2 GB maximum limit.")}),
                [('Content-Type', 'application/json')],
                status=400,
            )

        IrAttachment = request.env['ir.attachment']
        fname, full_path = IrAttachment._get_path(b'', checksum)
        if not os.path.exists(full_path):
            IrAttachment._mark_for_gc(fname)
            dirname = os.path.dirname(full_path)
            os.makedirs(dirname, exist_ok=True)
            with open(full_path, 'wb') as fp:
                shutil.copyfileobj(stream, fp, length=65536)

        # Unlink existing attachment for this field if present
        existing_attachments = IrAttachment.search([
            ('res_model', '=', 'media.asset'),
            ('res_field', '=', 'file'),
            ('res_id', '=', asset.id),
        ])
        existing_attachments.unlink()

        # Create attachment via ORM without buffering whole payload in RAM
        attachment = IrAttachment.create({
            'name': filename,
            'res_model': 'media.asset',
            'res_field': 'file',
            'res_id': asset.id,
            'type': 'binary',
        })
        models.Model.write(attachment, {
            'store_fname': fname,
            'checksum': checksum,
            'file_size': file_size,
        })

        asset.invalidate_recordset(['file'])
        asset.write({
            'file_name': filename,
        })
        asset._compute_file_size()

        return request.make_response(
            json.dumps({'file_name': filename}),
            [('Content-Type', 'application/json')],
        )


