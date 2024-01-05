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
from datetime import timedelta
from odoo import api, fields, models


class MailingList(models.Model):
    """Inherits the model mailing.list"""
    _inherit = 'mailing.list'

    mail_contact = fields.Boolean(
        string="Enable Mail on Subscription",
        help="Enable to send the mail to the contact when subscribed")
    template_id = fields.Many2one('drip.template', string="Select Template",
                                  help="Template to send to contact "
                                       "when subscribed")
    mass_mailing_enable = fields.Boolean(
        string="Enable Mass Mailing",
        help="Enable Drip Mass Mailing feature")
    start_date = fields.Date(string="Start Date", help="Start date to send to")
    end_date = fields.Date(string="End Date", help="End date to send to")
    server_id = fields.Many2one('ir.mail_server', string="Outgoing Mail Server",
                                help="Outgoing Mail Server to send to")
    template_ids = fields.One2many('mailing.list.templates', 'mailing_id',
                                   string="Drip Templates",
                                   help="Drip Templates to send")
    drip_count = fields.Integer(string="Drip Count",
                                help="Number of count of drips send",
                                compute="_compute_drip_count")

    def _action_drip_mass_mailing(self):
        """
        This is the method _action_drip_mass_mailing which is here used to make
        the function work of drip mass mailing from the scheduled action
        """
        mailing_list_records = self.env['mailing.list'].search([
            ('mass_mailing_enable', '=', True),
            ('end_date', '>=', fields.date.today())
        ])
        for record in mailing_list_records:
            start_date = fields.Date.from_string(record.start_date)
            for template in record.template_ids:
                drip_date = start_date + timedelta(template.days_after)
                if fields.date.today() == drip_date and record.contact_ids:
                    mail_template = self.env.ref(
                        'odoo_drip_email_marketing.drip_mass_mail_email_template')
                    attachment_data = [(6, 0, [attachment.id for attachment in
                                               template.template_id.attachment_ids])]
                    recipients = [contact.email for contact in
                                  record.contact_ids.filtered(
                                      lambda rec: not rec.is_blacklisted)]
                    email_values = {
                        'subject': template.template_id.name,
                        'body_html': template.template_id.mail_body,
                        'email_to': ', '.join(recipients),
                        'attachment_ids': attachment_data,
                    }
                    history_data = [{
                        'name': template.name,
                        'contact_id': contact.id,
                        'mailing_id': record.id,
                        'template_id': template.template_id.id,
                        'send_date': fields.Date.today()
                    } for contact in record.contact_ids.filtered(
                        lambda rec: not rec.is_blacklisted)]
                    mail_template.send_mail(record.id,
                                            force_send=True,
                                            email_values=email_values)
                    self.env['drip.mailing.history'].create(history_data)

    def get_drip_history(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Drip History',
            'view_mode': 'tree,form',
            'res_model': 'drip.mailing.history',
            'domain': [('mailing_id', '=', self.id)],
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
                [('mailing_id', '=', record.id)])
            record.drip_count = count
