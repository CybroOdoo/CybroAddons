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

from odoo import models
from odoo.exceptions import UserError
from odoo.addons.mail.tools.parser import parse_res_ids


class MailFollowersEdit(models.TransientModel):
    """ Inherited the class and added bool param in the function to determine
    it is an automated or manual follower add process """

    _inherit = 'mail.followers.edit'

    def edit_followers(self):
        """Edit followers on selected records."""
        for wizard in self:
            res_ids = parse_res_ids(wizard.res_ids, self.env)
            documents = self.env[wizard.res_model].browse(res_ids)
            if not documents:
                raise UserError(self.env._("No documents found for the selected records."))
            if wizard.operation == "remove":
                documents.message_unsubscribe(partner_ids=wizard.partner_ids.ids)
            else:
                if not self.env.user.email:
                    raise UserError(
                        self.env._(
                            "Unable to post message, please configure the sender's email address."
                        )
                    )
                documents.message_subscribe(partner_ids=wizard.partner_ids.ids, is_auto=False)
                if wizard.notify:
                    model_name = self.env["ir.model"]._get(wizard.res_model).display_name
                    message_values = wizard._prepare_message_values(documents, model_name)
                    message_values["partner_ids"] = wizard.partner_ids.ids
                    documents[0].message_notify(**message_values)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": self.env._("Followers updated") if len(wizard) > 1 else (
                    self.env._("Followers added") if wizard.operation == "add" else self.env._("Followers removed")
                ),
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def _prepare_message_values(self, documents, model_name):
        """Prepare notification message values."""
        return {
            "body": (len(documents) > 1 and (", ".join(documents.mapped('display_name')) + "\n") or "") + (
                    self.message or ""),
            "email_add_signature": False,
            "email_from": self.env.user.email_formatted,
            "email_layout_xmlid": len(
                documents) > 1 and "mail.mail_notification_multi_invite" or "mail.mail_notification_invite",
            "model": self.res_model,
            "reply_to": self.env.user.email_formatted,
            "reply_to_force_new": True,
            "subject": len(documents) > 1 and self.env._(
                "Invitation to follow %(document_model)s.",
                document_model=model_name,
            ) or self.env._(
                "Invitation to follow %(document_model)s: %(document_name)s",
                document_model=model_name,
                document_name=documents.display_name,
            )
        }
