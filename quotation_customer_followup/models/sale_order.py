# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Prasudhi A (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class SaleOrder(models.Model):
    """This model  used  to  send a warning , followup mail to
    customer based on quotation status and quotation expiry."""
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _compute_sale_warning_text(self):
        """Function to autofill quotation expiry date based on calculating
        order_date and user expected date"""
        res = super()._compute_sale_warning_text()
        if self.partner_id.quotation_expiry_days:
            self.validity_date = fields.Date.add(
                self.date_order,
                days=int(self.partner_id.quotation_expiry_days))
        else:
            self.validity_date = fields.Date.add(
                self.date_order,
                days=int(self.env['ir.config_parameter'].sudo().get_param(
                    'res.config.settings.expiry_days')))
            return res

    def process_scheduler_quotation(self):
        """Function to calculate the expiry date of quotation and send the
        email to customer"""
        parameter = self.env['ir.config_parameter'].sudo()
        template_id = parameter.get_param('res.config.settings.expiry_mail_template')
        if not template_id:
            return
        email_template = self.env['mail.template'].browse(int(template_id))
        if not email_template.exists():
            return
        today = fields.Date.today()
        orders = self.search([
            ('state', '=', 'sent'),
            ('validity_date', '<=', today),
        ])

        for rec in orders:
            if rec.partner_id.email:
                email_template.send_mail(
                    rec.id,
                    email_values={
                        'email_to': rec.partner_id.email,
                        'email_from': rec.user_id.partner_id.email,
                    },
                    force_send=True
                )
    def followup_scheduler_queue(self):
        """Function to send  mail to customer based on if state does not
        change between user expected days"""
        parameter = self.env['ir.config_parameter'].sudo()
        days = int(parameter.get_param('res.config.settings.days', 0))
        template_id = parameter.get_param('res.config.settings.mail_template')
        if not template_id or not days:
            return
        email_template = self.env['mail.template'].browse(int(template_id))
        if not email_template.exists():
            return
        limit_date = fields.Datetime.now() - relativedelta(days=days)
        orders = self.search([
            ('state', '=', 'sent'),
            ('date_order', '<=', limit_date),
        ])
        for rec in orders:
            if rec.partner_id.email:
                email_template.send_mail(
                    rec.id,
                    email_values={
                        'email_to': rec.partner_id.email,
                        'email_from': rec.user_id.partner_id.email,
                    },
                    force_send=True
                )
