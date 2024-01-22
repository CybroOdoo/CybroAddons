# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class SaleOrder(models.Model):
    """This model  used  to  send a warning , followup mail to
    customer based on quotation status and quotation expiry."""
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner_id_warning(self):
        """Function to autofill quotation expiry date based on calculating
        order_date and user expected date"""
        res = super()._onchange_partner_id_warning()
        if self.partner_id.quotation_expiry_days:
            self.validity_date = fields.Date.add(
                self.date_order,
                days=int(self.partner_id.quotation_expiry_days))
        else:
            self.validity_date = fields.Date.add(
                self.date_order,
                days=int(self.env['ir.config_parameter'].get_param(
                    'res.config.settings.expiry_days')))
            return res

    def process_scheduler_quotation(self):
        """Function to calculate the expiry date of quotation and send the
        email to customer"""
        template = self.env['ir.config_parameter'].get_param(
            'res.config.settings.expiry_mail_template')
        email_template = self.env['mail.template'].browse(int(template))
        for rec in self.search([('state', '=', 'sent'),
                                ('validity_date', '=', fields.date.today())]):
            email_template.send_mail(self.id, email_values={
                'email_to': rec.partner_id.email,
                'email_from': rec.user_id.login}, force_send=True)

    def followup_scheduler_queue(self):
        """Function to send  mail to customer based on if state does not
        change between user expected days"""
        parameter = self.env['ir.config_parameter']
        days = parameter.get_param(
            'res.config.settings.days')
        template = parameter.get_param(
            'res.config.settings.mail_template')
        email_template = self.env['mail.template'].browse(int(template))
        dates = fields.Date.subtract(fields.date.today(), days=int(days))
        start_date = fields.Datetime.to_datetime(dates)
        end_date = start_date + relativedelta(hour=23, second=59, minute=59)
        for rec in self.search([
            ('state', '=', 'sent'), ('date_order', '>', start_date), (
                    'date_order', '<', end_date)]):
            email_template.send_mail(self.id, email_values={
                'email_to': rec.partner_id.email,
                'email_from': rec.user_id.login}, force_send=True)
