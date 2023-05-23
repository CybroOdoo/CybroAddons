# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swetha Anand (odoo@cybrosys.com)
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
###############################################################################
from odoo.exceptions import AccessError
from odoo.http import request
from odoo import _
from odoo.addons.mail.controllers.discuss import DiscussController


class DiscussController(DiscussController):
    """This class is called to override mail_attachment_upload()."""

    def mail_attachment_upload(self, ufile, thread_id,
                               thread_model, is_pending=False, **kwargs):
        """
        Override the function mail_attachment_upload() to include
        a check to see if the size of the attachment exceeds
        the user-assigned maximum size. If true, an error
        message is displayed.
        """
        channel_member = request.env['mail.channel.member']
        set_restriction = request.env.user.set_restriction
        max_size = request.env.user.max_size * 1024 * 1024
        if thread_model == 'mail.channel':
            channel_member = request.env['mail.channel.member']. \
                _get_as_sudo_from_request_or_raise(
                request=request, channel_id=int(thread_id))
        vals = {
            'name': ufile.filename,
            'raw': ufile.read(),
            'res_id': int(thread_id),
            'res_model': thread_model,
        }
        if is_pending and is_pending != 'false':
            # Add this point, the message related to the uploaded file does
            # not exist yet, so we use those placeholder values instead.
            vals.update({
                'res_id': 0,
                'res_model': 'mail.compose.message',
            })
        if channel_member.env.user.share:
            # Only generate the access token if absolutely
            # necessary (= not for internal user).
            vals['access_token'] = \
                channel_member.env['ir.attachment']._generate_access_token()
        try:
            attachment = channel_member.env['ir.attachment'].create(vals)
            attachment._post_add_create()
            attachmentData = {
                'filename': ufile.filename,
                'id': attachment.id,
                'mimetype': attachment.mimetype,
                'name': attachment.name,
                'size': attachment.file_size
            }
            if attachment.access_token:
                attachmentData['accessToken'] = attachment.access_token
            if set_restriction:
                if attachmentData['size'] > max_size:
                    attachmentData = {'error': _('Attachment'
                                                 ' size cannot exceed %s MB.'
                                                 ) % request.env.user.max_size}
                    attachment.unlink()
        except AccessError:
            attachmentData = {'error': _("You are not allowed to "
                                         "upload an attachment here.")}
        return request.make_json_response(attachmentData)
