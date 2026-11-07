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
import base64
import io
import zipfile
from odoo import http
from odoo.http import request


class DownloadAllAttachments(http.Controller):
    """Controller for downloading all attachments as a single zip file"""

    @http.route(['/chatter/attachments/download/zip', '/chatter/attach_load/zip'], type='http', auth="user",
                cors="*", csrf=False)
    def download_attachments(self, res_id=None, res_model=None, **kwargs):
        """
        Download all attachments as a single zip file.
        """
        raw_res_id = res_id or request.params.get('res_id')
        model_name = res_model or request.params.get('res_model')
        if not raw_res_id:
            return request.make_response(b'', headers=[('Content-Type', 'application/zip')])
        try:
            chatter_id = int(raw_res_id)
        except (ValueError, TypeError):
            chatter_id = False
        if not chatter_id:
            return request.make_response(b'', headers=[('Content-Type', 'application/zip')])
        domain = [('res_id', '=', chatter_id)]
        if model_name:
            domain.append(('res_model', '=', model_name))
        else:
            domain.append(('res_model', '!=', 'account.move'))
        attachments = request.env['ir.attachment'].sudo().search(domain)
        if attachments:
            zip_filename = f'attachments_{model_name or "chatter"}_{chatter_id}.zip'
            zip_data = io.BytesIO()
            with zipfile.ZipFile(zip_data, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for attachment in attachments:
                    try:
                        raw_val = attachment.raw
                        if hasattr(raw_val, 'content'):
                            content = raw_val.content
                        elif hasattr(raw_val, 'read'):
                            content = raw_val.read()
                        elif raw_val and isinstance(raw_val, (bytes, bytearray)):
                            content = bytes(raw_val)
                        elif attachment.datas:
                            content = base64.b64decode(attachment.datas)
                        else:
                            content = b''
                    except Exception as e:
                        content = b''
                    if not isinstance(content, bytes):
                        try:
                            content = bytes(content)
                        except Exception:
                            content = b''
                    att_name = attachment.name or f'attachment_{attachment.id}'
                    zipf.writestr(att_name, content)
            response = request.make_response(
                zip_data.getvalue(),
                headers=[
                    ('Content-Type', 'application/zip'),
                    ('Content-Disposition', f'attachment; filename="{zip_filename}"'),
                ]
            )
            zip_data.close()
            return response
        return request.make_response(b'', headers=[('Content-Type', 'application/zip')])
