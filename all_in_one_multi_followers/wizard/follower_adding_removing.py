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
from lxml import etree
from lxml.html import builder as html

from odoo import api, fields, models
from odoo.exceptions import UserError


class FollowerAddingRemoving(models.TransientModel):
    """Wizard to add or remove followers for the selected records."""
    _name = 'follower.adding.removing'
    _description = 'Follower Adding Removing'

    res_id = fields.Integer('Related Document ID',
                            help='Id of the followed resource')
    type = fields.Selection(
        [('add', 'Add Followers'), ('remove', 'Remove Followers')],
        string="Action Type", help='Select the action type',
        default='add')
    partner_ids = fields.Many2many('res.partner', string='Partners',
                                   help='Select the partners to add to or'
                                        ' remove from followers')
    send_mail = fields.Boolean(string='Send Email', default=True,
                               help="If checked, the partners will receive an "
                                    "email warning they have been added in "
                                    "the document's followers.")
    message = fields.Html(help='Invite/ Remove mailing message.')

    def action_submit(self):
        """
        Adds or removes followers from records based on user input when the
        submit button is clicked.
        """
        model_name_key = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])
        model_info = self.env['ir.model'].search(
            [('model', '=', model_name_key)],
            limit=1) if model_name_key else self.env['ir.model']
        email_from = self.env.user.email_formatted
        title = [
            active_rec.display_name
            for active_rec in self.env[model_name_key].browse(active_ids)
        ] if model_name_key and active_ids else []

        for wizard in self:
            if model_name_key and active_ids:
                records = self.env[model_name_key].browse(active_ids)
                if not hasattr(records, 'message_subscribe'):
                    raise UserError(self.env._(
                        "The selected model '%(model)s' does not support followers.",
                        model=model_info.display_name or model_name_key,
                    ))
                if wizard.type == 'add':
                    records.message_subscribe(partner_ids=wizard.partner_ids.ids)
                elif wizard.type == 'remove':
                    records.message_unsubscribe(partner_ids=wizard.partner_ids.ids)

            new_partners = wizard.partner_ids
            model_name = model_info.display_name if model_info else ''
            if wizard.send_mail and wizard.message and wizard.message != '<br>':
                msg_vals = wizard._prepare_message_values(
                    title, model_name, email_from, new_partners,
                )
                if msg_vals.get('email_to'):
                    self.env['mail.mail'].create(msg_vals).send()

    @api.onchange('type')
    def _onchange_type(self):
        """
        Updates the 'message' field based on the selected type (add or remove) when
        the 'type' field is changed.
        """
        user_name = self.env.user.display_name
        model = self.env.context.get('active_model')
        document = self.env['ir.model']._get(model).display_name if model else ''
        active_ids = self.env.context.get('active_ids', [])
        title_list = [
            active_rec.display_name
            for active_rec in self.env[model].browse(active_ids)
        ] if model else []
        title = ', '.join(title_list)
        if self.type == 'add':
            text = self.env._(
                '%(user_name)s has invited you to follow the %(document)s document: %(title)s',
                user_name=user_name,
                document=document,
                title=title,
            )
        else:
            text = self.env._(
                '%(user_name)s has removed you from following the %(document)s document: %(title)s',
                user_name=user_name,
                document=document,
                title=title,
            )
        message = html.DIV(
            html.P(self.env._('Hello,')),
            html.P(text),
        )
        self.message = etree.tostring(message, encoding='unicode', method='html')

    def _prepare_message_values(self, title, model_name, email_from,
                                new_partners):
        """
        Prepares the necessary email values for sending a notification about
        following or unfollowing a document.
        """
        title_str = ', '.join(title) if isinstance(title, list) else (title or '')
        emails = [email for email in new_partners.mapped('email') if email]
        return {
            'subject': self.env._(
                'Document Follower Update - %(document_model)s: %(document_name)s',
                document_model=model_name or '',
                document_name=title_str,
            ),
            'body_html': self.message,
            'record_name': title_str,
            'email_from': email_from,
            'email_to': ','.join(emails),
            'reply_to': email_from,
            'reply_to_force_new': True,
            'email_add_signature': True,
        }
