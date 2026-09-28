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
import hashlib
import os
import shutil
import unicodedata
from odoo import _, http, tools
from odoo.exceptions import AccessError
from odoo.http import request
import json

class MediaAssetUploadController(http.Controller):
    """Direct multipart upload for media.asset's file field.

    Bypasses the standard binary widget's call_kw/base64 flow, whose
    request body is size-checked before the web.max_file_upload_size
    system parameter is applied. Modified to support up to 50GB file sizes
    without causing MemoryError in the Odoo server.
    """

    @http.route('/media_repository/asset/upload_file', type='http', auth='user', methods=['POST'], max_content_length=53687091200)
    def upload_media_asset_file(self, model, id, ufile, **kwargs):
        if model != 'media.asset':
    
            return request.make_response(json.dumps({'error': _("Invalid model.")}), [('Content-Type', 'application/json')])

        asset = request.env['media.asset'].browse(int(id))
        try:
            asset.check_access('write')
        except AccessError:
            return request.make_response(json.dumps(
                {'error': _("You are not allowed to upload a file on this record.")}), [('Content-Type', 'application/json')])

        files = request.httprequest.files.getlist('ufile')
        if not files:
            return request.make_response(json.dumps({'error': _("No file uploaded.")}), [('Content-Type', 'application/json')])
        uploaded_file = files[0]

        filename = uploaded_file.filename
        if request.httprequest.user_agent.browser == 'safari':
            filename = unicodedata.normalize('NFD', filename)

        attachments = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'media.asset'),
            ('res_field', '=', 'file'),
            ('res_id', '=', asset.id),
        ])
        attachments.unlink()


        filestore_path = tools.config.filestore(request.env.cr.dbname)
        temp_path = os.path.join(filestore_path, f'tmp_upload_{asset.id}')

        with open(temp_path, 'wb') as f:
            uploaded_file.save(f)

        sha1 = hashlib.sha1()
        file_size = 0
        with open(temp_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sha1.update(chunk)
                file_size += len(chunk)

        checksum = sha1.hexdigest()

        final_dir = os.path.join(filestore_path, checksum[:2])
        os.makedirs(final_dir, exist_ok=True)
        final_path = os.path.join(final_dir, checksum)
        
        if os.path.exists(final_path):
            os.remove(temp_path)
        else:
            shutil.move(temp_path, final_path)

        attachment = request.env['ir.attachment'].sudo().create({
            'name': filename,
            'res_model': 'media.asset',
            'res_field': 'file',
            'res_id': asset.id,
            'type': 'binary',
        })
        

        safe_file_size = min(file_size, 2147483647)
        store_fname = f"{checksum[:2]}/{checksum}"
        request.env.cr.execute("""
            UPDATE ir_attachment
            SET store_fname = %s, checksum = %s, file_size = %s
            WHERE id = %s
        """, (store_fname, checksum, safe_file_size, attachment.id))

        attachment.invalidate_recordset()
        asset.invalidate_recordset(['file'])
        asset.file_name = filename
        asset._compute_file_size()
        asset.flush_recordset(['file_name', 'file_size'])

        return request.make_response(json.dumps({'file_name': filename}), [('Content-Type', 'application/json')])
