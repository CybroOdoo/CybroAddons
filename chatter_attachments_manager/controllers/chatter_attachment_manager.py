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
import zipfile
from datetime import datetime
from io import BytesIO

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request
from odoo.http.stream import content_disposition


class ChatterAttachmentManagerBinary(http.Controller):
    """Attachment downloading binary class."""

    @http.route(
        "/chatter_attachments_manager/download_document",
        type="http",
        auth="user",
    )
    def download_zip(self, **kwargs):
        """Download all chatter attachments belonging to a record
        as a zip file.
        """
        model = kwargs.get("param1", "")
        try:
            tab_id = int(kwargs.get("param2", 0))
        except (ValueError, TypeError):
            tab_id = 0

        if (
            not model
            or not isinstance(model, str)
            or not model.replace(".", "_").isidentifier()
        ):
            raise request.not_found()

        if model not in request.env or not tab_id:
            raise request.not_found()

        try:
            record = request.env[model].browse(tab_id)
            if not record.exists():
                raise request.not_found()
            record.check_access("read")
        except (AccessError, UserError):
            raise request.not_found()

        attachment_ids = request.env["ir.attachment"].search(
            [
                ("res_model", "=", model),
                ("res_id", "=", tab_id),
            ],
        )

        zip_filename = (
            f"{model}_{tab_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        )
        bit_io = BytesIO()

        with zipfile.ZipFile(bit_io, "w", zipfile.ZIP_DEFLATED) as zip_file:
            used_names = set()
            for attachment in attachment_ids:
                data = None
                if attachment.raw:
                    data = (
                        attachment.raw.content
                        if hasattr(attachment.raw, "content")
                        else bytes(attachment.raw)
                    )
                elif hasattr(attachment, "datas") and attachment.datas:
                    data = base64.b64decode(attachment.datas)
                elif hasattr(attachment, "store_fname") and attachment.store_fname:
                    try:
                        with open(
                            attachment._full_path(attachment.store_fname),
                            "rb",
                        ) as f:
                            data = f.read()
                    except OSError:
                        data = None

                if data is not None:
                    name = attachment.name or f"attachment_{attachment.id}"
                    original_name = name
                    counter = 1
                    while name in used_names:
                        base, ext = (
                            original_name.rsplit(".", 1)
                            if "." in original_name
                            else (original_name, "")
                        )
                        name = f"{base}_{counter}.{ext}" if ext else f"{base}_{counter}"
                        counter += 1
                    used_names.add(name)
                    zip_file.writestr(name, data)

        return request.make_response(
            bit_io.getvalue(),
            headers=[
                ("Content-Type", "application/zip"),
                ("Content-Disposition", content_disposition(zip_filename)),
            ],
        )
