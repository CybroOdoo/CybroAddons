# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Safa KB (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.exceptions import AccessError
from odoo.http import request
from odoo import _
from odoo.addons.mail.controllers.attachment import AttachmentController
from werkzeug.exceptions import NotFound
from odoo.addons.mail.tools.discuss import Store


class DiscussController(AttachmentController):
    def mail_attachment_upload(self, ufile, thread_id, thread_model,
                               is_pending=False, **kwargs):
        """ Shows warning if the attachment size exceeds the maximum size allowed """
        thread = self._get_thread_with_access_for_post(
            thread_model, thread_id, **kwargs)
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
            res = {
                'error': _('Attachment size cannot exceed %s MB.') % request.env.user.max_size
            }
            return request.make_json_response(res)

        vals = {
            "name": ufile.filename,
            "raw": file_content,
            "res_id": int(thread_id),
            "res_model": thread_model,
        }

        if company_id := thread._mail_get_companies()[thread.id]:
            vals["company_id"] = company_id.id
        elif cids := request.cookies.get("cids", False):
            active_company_ids = [int(cid) for cid in cids.split("-")]
            company_id = (
                request.env.user.company_id.id
                if request.env.user.company_id.id in active_company_ids
                else active_company_ids[0]
            )
            vals["company_id"] = company_id

        if is_pending and is_pending != "false":
            # At this point, the message related to the uploaded file does
            # not exist yet, so we use those placeholder values instead.
            vals.update(
                {
                    "res_id": 0,
                    "res_model": "mail.compose.message",
                }
            )

        try:
            # sudo: ir.attachment - posting a new attachment on an
            # accessible thread
            attachment = request.env["ir.attachment"].sudo().create(vals)
            attachment._post_add_create(**kwargs)
            res = {
                "data": {
                    "store_data": Store().add(
                        attachment,
                        extra_fields=request.env[
                            "ir.attachment"
                        ]._get_store_ownership_fields(),
                    ).get_result(),
                    "attachment_id": attachment.id,
                }
            }
        except AccessError:
            res = {
                "error": _("You are not allowed to upload an attachment here.")
            }

        return request.make_json_response(res)
