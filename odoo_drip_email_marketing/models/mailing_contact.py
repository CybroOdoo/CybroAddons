# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arjun S(odoo@cybrosys.com)
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
from odoo import api, fields, models


class MailingContact(models.Model):
    """Inherits the model mailing.contact"""
    _inherit = 'mailing.contact'

    name = fields.Char(required=True, string='Name', help="Name of the contact")
    email = fields.Char(required=True, string='Email',
                        help="Email address of the contact")
    drip_count = fields.Integer(string="Drip Count",
                                help="Number of count of drips send",
                                compute="_compute_drip_count")

    @api.model
    def create(self, vals_list):
        """
        This is the create method of mailing.contact which already exists here
        we are supering this create method as to send the email to the contact
        created that they are subscribed into this mailing list
        """
        res = super().create(vals_list)
        mailing_list = self.env['mailing.list'].browse(
            self.env.context.get('active_id'))
        if mailing_list.mail_contact:
            mail_template = self.env.ref(
                'odoo_drip_email_marketing.mail_list_subscription_email_template')
            attachments = mailing_list.template_id.attachment_ids
            attachment_data = [
                (6, 0, [attachment.id for attachment in attachments])]
            mail_template.send_mail(mailing_list.id, force_send=True,
                                    email_values={
                                        'attachment_ids': attachment_data,
                                        'email_to': res.email
                                    })
        return res

    def get_drip_history(self):
        """
        This is the method get_drip_history which is used to get the history of
        the dripped mass mailing of this contact
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Drip History',
            'view_mode': 'tree,form',
            'res_model': 'drip.mailing.history',
            'domain': [('contact_id', '=', self.id)],
            'context': "{'create': False, 'edit':True}"
        }

    @api.model
    def _compute_drip_count(self):
        """
        This is the method _compute_drip_count which is used to compute the
        value to the field drip_count
        """
        for record in self:
            count = record.env['drip.mailing.history'].search_count(
                [('contact_id', '=', record.id)])
            record.drip_count = count
