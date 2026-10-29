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
#############################################################################
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class SaleOrder(models.Model):
    """This model is used to send follow-up and expiry emails to
    customers based on quotation status and quotation expiry."""
    _inherit = 'sale.order'

    @api.depends('partner_id.quotation_expiry_days', 'date_order')
    def _compute_validity_date(self):
        """Compute the quotation validity date based on customer expiry days
        or the default expiry days configuration."""
        super()._compute_validity_date()
        expiry_days_config = self.env['ir.config_parameter'].sudo().get_int(
            'quotation_customer_followup.expiry_days'
        )
        for order in self:
            days = order.partner_id.quotation_expiry_days or expiry_days_config
            if days > 0:
                base_date = (
                    fields.Date.to_date(order.date_order)
                    if order.date_order
                    else fields.Date.context_today(order)
                )
                order.validity_date = fields.Date.add(base_date, days=days)

    def process_scheduler_quotation(self):
        """Function to calculate the expiry date of quotation and send the
        email to customer"""
        parameter = self.env['ir.config_parameter'].sudo()
        if not parameter.get_bool('quotation_customer_followup.expiry_enable'):
            return
        template_id = parameter.get_str('quotation_customer_followup.expiry_mail_template')
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
                email_from = (
                    rec.user_id.email_formatted
                    or rec.company_id.partner_id.email_formatted
                )
                email_values = {'email_to': rec.partner_id.email}
                if email_from:
                    email_values['email_from'] = email_from
                email_template.send_mail(
                    rec.id,
                    email_values=email_values,
                    force_send=True
                )

    def followup_scheduler_queue(self):
        """Function to send mail to customer based on if state does not
        change between user expected days"""
        parameter = self.env['ir.config_parameter'].sudo()
        if not parameter.get_bool('quotation_customer_followup.followup_enable'):
            return
        days = parameter.get_int('quotation_customer_followup.days')
        template_id = parameter.get_str('quotation_customer_followup.mail_template')
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
                email_from = (
                    rec.user_id.email_formatted
                    or rec.company_id.partner_id.email_formatted
                )
                email_values = {'email_to': rec.partner_id.email}
                if email_from:
                    email_values['email_from'] = email_from
                email_template.send_mail(
                    rec.id,
                    email_values=email_values,
                    force_send=True
                )

