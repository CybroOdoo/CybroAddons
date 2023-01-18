# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Noorjahan N A (<https://www.cybrosys.com>)
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
from odoo import models, fields


class MarkAsDone(models.TransientModel):
    _name = 'rfq.done'

    def compute_domain(self):
        return [('quote_id', '=', self.env.context.get('active_id'))]

    vendor_id = fields.Many2one('rfq.vendor.quote_history',
                                domain=compute_domain)
    quoted_price = fields.Monetary(currency_field='currency_id',
                                   related='vendor_id.quoted_price')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True,
                                  default=lambda
                                      self: self.env.user.company_id.currency_id,
                                  related='vendor_id.currency_id')
    estimate_date = fields.Date(related='vendor_id.estimate_date')

    def mark_as_done(self):
        """Marking the RFQ as done"""
        rfq_id = self.env['rfq.vendor'].search([
            ('id', '=', self._context.get('active_id'))])
        template_id = self.env.ref(
            'vendor_portal_odoo.email_template_vendor_rfq_mark_done').id
        context = {
            'name': self.vendor_id.vendor_id.name,
            'lang': self.vendor_id.vendor_id.lang,
            'price': self.vendor_id.quoted_price,
            'delivery_date': self.vendor_id.estimate_date,
            'currency_id': self.vendor_id.currency_id
        }
        email_values = {
            'email_to': self.vendor_id.vendor_id.email,
            'email_from': self.env.user.partner_id.email,
        }
        self.env['mail.template'].browse(template_id).with_context(
            context).send_mail(self.vendor_id.quote_id.id, email_values=email_values,
                               force_send=True)
        rfq_id.write({
            'approved_vendor_id': self.vendor_id.vendor_id.id,
            'state': 'done'
        })
