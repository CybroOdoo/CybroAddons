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
import ast
import base64
from datetime import datetime
from io import BytesIO
import logging
import zipfile

from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition

_logger = logging.getLogger(__name__)


class Binary(http.Controller):
    """Attachment downloading binary class"""

    @http.route('/web/binary/download_document', type='http',
                auth="user")
    def download_document(self, tab_id):
        """Download attachment method with access checks and safe file reading"""
        try:
            new_tab = ast.literal_eval(tab_id)
            if isinstance(new_tab, int):
                new_tab = [new_tab]
            elif not isinstance(new_tab, (list, tuple)):
                return request.not_found()
        except (ValueError, SyntaxError):
            return request.not_found()

        attachment_ids = request.env['ir.attachment'].browse(new_tab).exists()
        if not attachment_ids:
            return request.not_found()

        # Check access rights: ensure user has permission to read the requested attachments
        if hasattr(attachment_ids, 'check_access'):
            attachment_ids.check_access('read')
        else:
            attachment_ids.check_access_rights('read')
            attachment_ids.check_access_rule('read')

        zip_filename = "%s.zip" % datetime.now()
        bit_io = BytesIO()
        with zipfile.ZipFile(bit_io, "w", zipfile.ZIP_DEFLATED) as zip_file:
            used_names = set()
            for attachment in attachment_ids:
                base_name = attachment.name or f"attachment_{attachment.id}"
                file_name = base_name
                counter = 1
                while file_name in used_names:
                    name_part, dot, ext = base_name.rpartition('.')
                    if dot:
                        file_name = f"{name_part}_{counter}.{ext}"
                    else:
                        file_name = f"{base_name}_{counter}"
                    counter += 1
                used_names.add(file_name)

                # Safely read binary data through the ORM rather than direct filestore paths
                raw = attachment.raw
                if hasattr(raw, 'content'):
                    data = raw.content
                elif isinstance(raw, (bytes, bytearray)):
                    data = bytes(raw)
                elif attachment.datas:
                    data = base64.b64decode(attachment.datas)
                else:
                    data = b''
                zip_file.writestr(file_name, data)

        return request.make_response(
            bit_io.getvalue(),
            headers=[
                ('Content-Type', 'application/x-zip-compressed'),
                ('Content-Disposition', content_disposition(zip_filename)),
            ],
        )
