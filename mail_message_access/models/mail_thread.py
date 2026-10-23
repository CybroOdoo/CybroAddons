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
from odoo import _, models
from odoo.exceptions import AccessError
from odoo.http import request


class MailThread(models.AbstractModel):
    """Inherits mail.thread to restrict message posting and note logging based on access rights."""
    _inherit = 'mail.thread'

    def _check_mail_message_access(self, subtype_xmlid=None, subtype_id=False, message_type='notification', **kwargs):
        """Validate whether the current user has permission to post a message or log a note."""
        # Field tracking and automated system notifications skip manual chatter restriction
        if message_type in ('notification', 'user_notification', 'auto_comment', 'tracking') or kwargs.get('tracking_values'):
            return

        # Determine the acting user: prioritize HTTP request user when executed under sudo via controller
        user = self.env.user
        if self.env.su and request and hasattr(request, 'env') and request.env and not request.env.is_superuser():
            user = request.env.user

        # Superuser and system administrators bypass the restriction
        if not user or user._is_system() or user._is_admin():
            return

        # Non-internal users (e.g. portal / public) are not governed by internal chatter button rules
        if not user.has_group('base.group_user'):
            return

        # Resolve subtype to check whether this is Send Message or Log Note
        mt_comment_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_comment')
        mt_note_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')

        is_comment = (
            subtype_xmlid == 'mail.mt_comment'
            or (subtype_id and subtype_id == mt_comment_id)
        )
        is_note = (
            subtype_xmlid == 'mail.mt_note'
            or (subtype_id and subtype_id == mt_note_id)
            or (not subtype_id and not subtype_xmlid and message_type == 'comment')
        )

        if is_comment and not user.has_group('mail_message_access.group_allow_send_message_btn'):
            raise AccessError(_("You are not allowed to send messages in the chatter."))

        if is_note and not user.has_group('mail_message_access.group_allow_log_note_btn'):
            raise AccessError(_("You are not allowed to log notes in the chatter."))

    def message_post(self, *, subtype_xmlid=None, subtype_id=False, message_type='notification', **kwargs):
        """Override message_post to enforce chatter access permissions."""
        self._check_mail_message_access(
            subtype_xmlid=subtype_xmlid,
            subtype_id=subtype_id,
            message_type=message_type,
            **kwargs,
        )
        return super().message_post(
            subtype_xmlid=subtype_xmlid,
            subtype_id=subtype_id,
            message_type=message_type,
            **kwargs,
        )
