# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from lxml import etree
from lxml.html import builder as html
from odoo import api, fields, models, _


class FollowerAddingRemoving(models.TransientModel):
    """Creating a popup wizard to adding or removing the followers in to
     the model"""
    _name = 'follower.adding.removing'
    _description = 'Follower Adding Removing'

    res_id = fields.Integer('Related Document ID',
                            help='Id of the followed resource')
    type = fields.Selection(
        [('add', 'Add Followers'), ('remove', 'Remove Followers')],
        string="Action Type", help='Select the action type',
        default='add')
    partner_ids = fields.Many2many('res.partner', string='Partners',
                                   help='Select the partners to add or'
                                        ' remove to the followers')
    send_mail = fields.Boolean(string='Send Email', default=True,
                               help="If checked, the partners will receive an "
                                    "email warning they have been added in "
                                    "the document's followers.")
    message = fields.Html(string='Message', help='Invite/ Remove mailing '
                                                 'message.')

    def action_submit(self):
        """
        Adds or removes followers from records based on user input when the
        submit button is clicked.

        - Retrieves the model information for the current active model (the one
          from which the action is triggered).
        - Based on the action type (`add` or `remove`), it either subscribes or
          unsubscribes the selected followers (partners) to/from the records.
        - If the `send_mail` flag is enabled and a message is provided, an email
          notification is sent to the new followers.

        Key Steps:
        1. Retrieve the active model and its records using the context's
           `active_model` and `active_ids`.
        2. If the action type is 'add', the selected partners (followers) are
           subscribed to the record via `message_subscribe`.
        3. If the action type is 'remove', the selected partners are unsubscribed
           via `message_unsubscribe`.
        4. If email notifications are enabled (`send_mail` is True) and a message
           is provided, an email is composed and sent to the new followers.

        Returns:
        None
        """
        model_info = self.env['ir.model'].search(
            [('model', '=', self.env.context.get('active_model'))],
            limit=1)
        email_from = self.env.user.email_formatted
        title = [active_model.display_name for active_model in
                 self.env[self.env.context.get('active_model')].browse(
                     self.env.context.get('active_ids'))]
        for record_id in self.env.context.get('active_ids'):
            record = self.env[self.env.context.get('active_model')].browse(
                record_id)
            if self.type == 'add':
                record.message_subscribe(partner_ids=self.partner_ids.ids)
            elif self.type == 'remove':
                record.message_unsubscribe(partner_ids=self.partner_ids.ids)
        new_partners = self.partner_ids
        model_name = model_info.display_name
        if self.send_mail and self.message and not self.message == '<br>':
            self.env['mail.mail'].create(
                self._prepare_message_values(title, model_name, email_from,
                                             new_partners)
            ).send()

    @api.onchange('type')
    def _onchange_type(self):
        """
            Updates the 'message' field based on the selected type (add or remove) when
            the 'type' field is changed.

            This method is triggered automatically when the 'type' field is updated
            by the user. It generates a message to reflect whether the user is adding
            or removing followers from a document, and then updates the 'message'
            field of the current record with this information.

            Key Steps:
            1. Retrieves the name of the current user (`user_name`) and the active
               document's model (`active_model`) from the context.
            2. Fetches the display name of the document (record) and creates a message
               informing the user whether they are being invited to follow or are being
               removed from following the document.
            3. The message is formatted as HTML using the `html.DIV` and `html.P` elements,
               and is then serialized to a string and stored in the 'message' field.

            Example:
            - If the 'type' is 'add':
              "John Doe has invited you to follow the Sales Order document: SO001".
            - If the 'type' is 'remove':
              "John Doe has removed you from following the Sales Order document: SO001".

            Returns:
            None
        """
        user_name = self.env.user.display_name
        model = self.env.context.get('active_model')
        document = self.env['ir.model']._get(model).display_name
        title = [active_model.display_name for active_model in
                 self.env[model].browse(self.env.context.get('active_ids'))]
        if self.type == 'add':
            msg_fmt = _(
                f'{user_name} has invited you to follow the {document} '
                f'document: {title}')
        else:
            msg_fmt = _(
                f'{user_name} has removed you from following the {document} '
                f'document: {title}')
        text = msg_fmt % locals()
        message = html.DIV(
            html.P(_('Hello,')),
            html.P(text)
        )
        self.message = etree.tostring(message, encoding='unicode', method='html')

    def _prepare_message_values(self, title, model_name, email_from,
                                new_partners):
        """
        Prepares the necessary email values for sending a notification about
        following or unfollowing a document.

        This method is responsible for generating the content of the email that
        will be sent when followers are added or removed from a document. The email
        contains details such as the document's model and title, the sender's email
        address, and the recipients' email addresses.

        Parameters:
        - title (str): The display name or title of the document being followed
          or unfollowed.
        - model_name (str): The display name of the model (e.g., "Sales Order",
          "Purchase Order").
        - email_from (str): The formatted email address of the current user (the sender).
        - new_partners (recordset): A recordset of partners (followers) to whom
          the email will be sent.

        Returns:
        dict: A dictionary of email values containing the following keys:
        - `subject`: The subject line of the email, including the document model
          and title.
        - `body_html`: The HTML content of the email, using the message field
          defined in the current record.
        - `record_name`: The name of the document being followed/unfollowed.
        - `email_from`: The sender's email address.
        - `email_to`: A comma-separated list of email addresses of the new partners.
        - `reply_to`: The sender's email address for reply purposes.
        - `reply_to_force_new`: A flag to force new email threads for replies.
        - `email_add_signature`: A flag to include the user's email signature in
          the message.

        This method is designed to format and structure the email data so that it
        can be sent out to notify partners of changes in document followers.
        """
        email_values = {
            'subject': _(
                'The Document follow %(document_model)s: %(document_name)s',
                document_model=model_name,
                document_name=title),
            'body_html': self.message,
            'record_name': title,
            'email_from': email_from,
            'email_to': ','.join(new_partners.mapped('email')),
            'reply_to': email_from,
            'reply_to_force_new': True,
            'email_add_signature': True,
        }
        return email_values




