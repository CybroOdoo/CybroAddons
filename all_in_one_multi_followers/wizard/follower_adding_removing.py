# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Junaidul Ansar M (odoo@cybrosys.com)
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
        """Adding or removing the followers when clicking the submit button"""
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
        """Update a message based on the selected type.

    This method is triggered when the 'type' field is changed. It generates
    a message to inform the user about the type change, and the message is
    displayed in the 'message' field of the current record.
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
        self.message = etree.tostring(message)

    def _prepare_message_values(self, title, model_name, email_from,
                                new_partners):
        """Prepares the message values to send in the email"""
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
