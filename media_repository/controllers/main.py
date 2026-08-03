# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhammed Muflih c(odoo@cybrosys.com)
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
import unicodedata
from odoo import _, http
from odoo.exceptions import AccessError
from odoo.http import request


class MediaAssetUploadController(http.Controller):
    """Direct multipart upload for media.asset's file field.

    Bypasses the standard binary widget's call_kw/base64 flow, whose
    request body is size-checked before the web.max_file_upload_size
    system parameter is applied, hard-capping uploads at ~95MB.
    """

    @http.route('/media_repository/asset/upload_file', type='http', auth='user', methods=['POST'])
    def upload_media_asset_file(self, model, id, ufile, **kwargs):
        if model != 'media.asset':
            return request.make_json_response({'error': _("Invalid model.")})

        asset = request.env['media.asset'].browse(int(id))
        try:
            asset.check_access('write')
        except AccessError:
            return request.make_json_response(
                {'error': _("You are not allowed to upload a file on this record.")})

        filename = ufile.filename
        if request.httprequest.user_agent.browser == 'safari':
            filename = unicodedata.normalize('NFD', filename)

        attachments = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'media.asset'),
            ('res_field', '=', 'file'),
            ('res_id', '=', asset.id),
        ])
        attachments.unlink()

        request.env['ir.attachment'].sudo().create({
            'name': filename,
            'raw': ufile.read(),
            'res_model': 'media.asset',
            'res_field': 'file',
            'res_id': asset.id,
        })

        asset.invalidate_recordset(['file'])
        asset.file_name = filename
        asset._compute_file_size()
        asset.flush_recordset(['file_name', 'file_size'])

        return request.make_json_response({'file_name': filename})
