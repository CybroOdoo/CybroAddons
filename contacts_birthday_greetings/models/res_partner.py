# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra K (odoo@cybrosys.com)
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


class ResPartner(models.Model):
    """ Inherits partner and adds date of birth and age. """
    _inherit = 'res.partner'

    date_of_birth = fields.Date(
        string="Date of Birth", help="Add the date of birth of the customer.")
    age = fields.Integer(
        string="Age", help="Age of the customer automatically calculates from the date of birth.")
    send_birthday_greetings = fields.Boolean(string="Send Birthday Greetings", default=True,
                                             help="To know whether the birthday greetings sent.")
    cbg_company_id = fields.Many2one('res.company', readonly=True, default=lambda self: self.env.company,
                                     help='TO get the company details in the email templates. ')

    @api.onchange('date_of_birth')
    def _onchange_date_of_birth(self):
        """ Updates the Age based on the field date_of_birth. """
        today_date = fields.Date.today()
        for partner in self:
            if partner.date_of_birth:
                date_of_birth = fields.Date.from_string(partner.date_of_birth)
                age = (today_date - date_of_birth).days / 365.0
                partner.age = age if age >= 0 else 0

    def action_send_email(self):
        """Sending greetings email to contacts on their birthday"""
        template_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'contacts_birthday_greetings.greetings_mail_template_id'))
        if not template_id:
            return
        today = fields.Date.today()
        partners = self.env['res.partner'].sudo().search([
            ('date_of_birth', '!=', False),
            ('date_of_birth', 'like', today.strftime('-%m-%d'))
        ])
        if not partners:
            return
        for partner in partners:
            partner._onchange_date_of_birth()
            subject = 'Happy Birthday ' + partner.name
            templates = self.env['mail.template'].sudo().browse(template_id)
            email_values = {'email_from': self.env.user.email or '',
                            'subject': subject,
                            'email_to': partner.email,
                            'recipient_ids': partner}
            templates.sudo().send_mail(
                partner.id, email_values = email_values, force_send=True, notif_layout='mail.mail_notification_light')
