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
from markupsafe import Markup, escape

from odoo import models


class AccountPaymentRegister(models.TransientModel):
    """ Inherit account.payment.register supering action_create_payments
        Sending mail for the first created invoice
    """
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        """ Method for creating payment """
        res = super().action_create_payments()

        active_model = self._context.get('active_model')
        active_ids = self._context.get('active_ids', [])
        invoices = self.env['account.move']
        if active_model == 'account.move':
            invoices = self.env['account.move'].browse(active_ids).exists()
        elif active_model == 'account.move.line':
            invoices = self.env['account.move.line'].browse(active_ids).exists().move_id

        if not invoices and self.communication:
            invoices = self.env['account.move'].search([('name', '=', self.communication)])

        for invoice_id in invoices:
            if invoice_id.is_first_invoice:
                mail_content = Markup(self.env._(
                    '<h3>First Payment Received!</h3><br/>Hi %(partner_name)s, <br/> '
                    'This is to notify that your first payment has been received. <br/><br/>'
                    'Please find the details below:<br/><br/>'
                    '<table><tr><td>Invoice Number</td><td>%(payment_reference)s</td></tr>'
                    '<tr><td>Date</td><td>%(invoice_date)s</td></tr>'
                    '<tr><td>Amount</td><td>%(amount_total)s</td></tr></table>',
                )) % {
                    'partner_name': escape(invoice_id.partner_id.name or ''),
                    'payment_reference': escape(invoice_id.payment_reference or invoice_id.name or ''),
                    'invoice_date': escape(str(invoice_id.invoice_date or '')),
                    'amount_total': escape(str(invoice_id.amount_total or 0.0)),
                }
                subject = self.env._('Payment Received: %s', invoice_id.payment_reference or invoice_id.name or '')
            elif invoice_id.fleet_rent_id:
                mail_content = Markup(self.env._(
                    '<h3>Recurrent Payment Received!</h3><br/>Hi %(partner_name)s, <br/> '
                    'This is to notify that your recurrent payment has been received. <br/><br/>'
                    'Please find the details below:<br/><br/>'
                    '<table><tr><td>Invoice Number</td><td>%(payment_reference)s</td></tr>'
                    '<tr><td>Contract Ref</td><td>%(contract_ref)s</td></tr>'
                    '<tr><td>Date</td><td>%(invoice_date)s</td></tr>'
                    '<tr><td>Amount</td><td>%(amount_total)s</td></tr></table>',
                )) % {
                    'partner_name': escape(invoice_id.partner_id.name or ''),
                    'payment_reference': escape(invoice_id.payment_reference or invoice_id.name or ''),
                    'contract_ref': escape(invoice_id.fleet_rent_id.name or ''),
                    'invoice_date': escape(str(invoice_id.invoice_date or '')),
                    'amount_total': escape(str(invoice_id.amount_total or 0.0)),
                }
                subject = self.env._('Payment Received: %s', invoice_id.payment_reference or invoice_id.name or '')
            else:
                continue

            main_content = {
                'subject': subject,
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': invoice_id.partner_id.email,
            }
            self.env['mail.mail'].create(main_content).send()
            invoice_id.message_post(body=mail_content, subject=main_content['subject'])
            if invoice_id.fleet_rent_id:
                invoice_id.fleet_rent_id.message_post(body=mail_content, subject=main_content['subject'])

        return res
