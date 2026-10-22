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
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.addons.mail.controllers.attachment import AttachmentController
from odoo.addons.mail.tools.discuss import Store


class DiscussController(AttachmentController):
    @http.route()
    def mail_attachment_upload(self, ufile, thread_id, thread_model,
                               is_pending=False, **kwargs):
        """ Shows warning if the attachment size exceeds the maximum size allowed """
        thread = request.env[thread_model].search([("id", "=", thread_id)])
        if not thread:
            raise NotFound()

        # Get user restriction settings
        set_restriction = request.env.user.set_restriction
        max_size = request.env.user.max_size * 1024 * 1024

        # Read file content
        file_content = ufile.read()
        file_size = len(file_content)

        # Check size restriction BEFORE creating attachment
        if set_restriction and file_size > max_size:
            attachment_data = {
                'size_error': request.env._('Attachment size cannot exceed %s MB.', request.env.user.max_size)
            }
            return request.make_json_response(attachment_data)

        vals = {
            "name": ufile.filename,
            "raw": file_content,
            "res_id": int(thread_id),
            "res_model": thread_model,
        }

        if is_pending and is_pending != "false":
            # Add this point, the message related to the uploaded file does
            # not exist yet, so we use those placeholder values instead.
            vals.update(
                {
                    "res_id": 0,
                    "res_model": "mail.compose.message",
                }
            )

        if request.env.user.share:
            # Only generate the access token if absolutely necessary
            # (= not for internal user).
            vals["access_token"] = request.env[
                "ir.attachment"]._generate_access_token()

        try:
            # sudo: ir.attachment - posting a new attachment on an
            # accessible thread
            attachment = request.env["ir.attachment"].sudo().create(vals)
            attachment._post_add_create(**kwargs)

            store = Store().add(
                attachment,
                lambda res: (
                    res.from_method("_store_attachment_fields", chatter_fields=not request.env.user.share),
                    res.from_method("_store_ownership_fields"),
                ),
            )
            attachment_data = {"data": {"store_data": store, "attachment_id": attachment.id}}

            if attachment.access_token:
                attachment_data["accessToken"] = attachment.access_token

        except AccessError:
            attachment_data = {
                "error": {
                    "message": request.env._("You are not allowed to upload an attachment here.")
                }
            }

        return request.make_json_response(attachment_data)
