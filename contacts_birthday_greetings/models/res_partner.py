# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models
import datetime


class ResPartner(models.Model):
    """This class inherit the 'res.partner' model to include
            additional fields for configuring birthday and age."""
    _inherit = 'res.partner'

    date_of_birth = fields.Date(string="Date of Birth", help="Date of birth field")
    age = fields.Integer(string="Age", readonly=True, compute="compute_age", store=True)
    send_bday_greetings = fields.Boolean(
        string="Send Birthday Greetings", default=True)
    cbg_company_id = fields.Many2one('res.company', readonly=True,
                                 default=lambda self: self.env.company)

    @api.depends('date_of_birth')
    def compute_age(self):
        """Method to calculate the age according to the birthday."""
        today_date = datetime.date.today()
        for partner in self:
            if partner.date_of_birth:
                date_of_birth = fields.Datetime.to_datetime(
                    partner.date_of_birth).date()
                total_age = ((today_date - date_of_birth).days / 365)
                partner.write({
                    'age': total_age
                })
            else:
                partner.write({
                    'age': 0
                })

    def action_send_email(self):
        """This function send birthday greetings email to contacts"""
        partners = self.env['res.partner'].sudo().search([])
        for partner in partners:
            if partner.date_of_birth:
                bdate = datetime.datetime.strptime(str(partner.date_of_birth),
                                                   '%Y-%m-%d').date()
                today = datetime.datetime.now().date()
                if bdate.month == today.month:
                    if bdate.day == today.day:
                        partners.compute_age()
                        template_id = int(
                            self.env['ir.config_parameter'].sudo().get_param(
                                'contacts_birthday_greetings'
                                '.greetings_mail_template_id'))
                        if template_id:
                            templates = self.env['mail.template'].sudo().browse(
                                template_id)
                            templates.sudo().send_mail(
                             partner.id, force_send=True,
                             email_layout_xmlid='mail.mail_notification_light')
