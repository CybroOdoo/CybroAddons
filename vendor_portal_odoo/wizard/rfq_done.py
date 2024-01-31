# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class RfqDone(models.TransientModel):
    """Done the Quotation"""
    _name = 'rfq.done'
    _description = 'Done RFQs'

    def _domain_history(self):
        """Domain for vendor_id"""
        return [('quote_id', '=', self.env.context.get('active_id'))]

    vendor_id = fields.Many2one('vendor.quote.history', string='Vendor',
                                domain=_domain_history, help='The history of'
                                                             'vendor quote')
    quoted_price = fields.Monetary(currency_field='currency_id',
                                   related='vendor_id.quoted_price',
                                   string='Quoted Price',
                                   help='Mention the price of the quote')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True,
                                  default=lambda
                                      self: self.env.user.company_id.currency_id,
                                  related='vendor_id.currency_id',
                                  help='Current users currency')
    estimate_date = fields.Date(related='vendor_id.estimate_date',
                                string='Estimate Date',
                                help='The estimated date of quote')

    def action_done(self):
        """Marking the RFQ as done"""
        rfq = self.env['vendor.rfq'].browse(self._context.get('active_id'))
        template_id = self.env.ref(
            'vendor_portal_odoo.email_template_vendor_rfq_mark_done').id
        context = {
            'name': self.vendor_id.vendor_id.name,
            'lang': self.vendor_id.vendor_id.lang,
            'price': self.vendor_id.quoted_price,
            'delivery_date': self.vendor_id.estimate_date,
            'currency_id': self.vendor_id.currency_id,
            'partner_to': self.vendor_id.id,
        }
        email_values = {
            'email_to': self.vendor_id.vendor_id.email,
            'email_from': self.env.user.partner_id.email,
        }
        self.env['mail.template'].browse(template_id).with_context(
            context).send_mail(self.vendor_id.quote_id.id,
                               email_values=email_values)
        rfq.write({'approved_vendor_id': self.vendor_id.vendor_id.id,
            'state': 'done'})
