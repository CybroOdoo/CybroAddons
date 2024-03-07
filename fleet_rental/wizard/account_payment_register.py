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
from odoo import models, _


class AccountPaymentRegister(models.TransientModel):
    """ Inherit account.payment.register supering action_create_payments
        Sending mail for the first created invoice
    """
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        res = super().action_create_payments()
        invoice_id = self.env['account.move'].search([('name', '=', self.communication)])
        if invoice_id.is_first_invoice:
            mail_content = _(
                '<h3>First Payment Received!</h3><br/>Hi %s, <br/> This is to notify that your first payment has '
                'been received. <br/><br/>'
                'Please find the details below:<br/><br/>'
                '<table><tr><td>Invoice Number<td/><td> %s<td/><tr/>'
                '<tr><td>Date<td/><td> %s <td/><tr/><tr><td>Amount <td/><td> %s<td/><tr/><table/>') % (
                               invoice_id.partner_id.name, invoice_id.payment_reference,
                               invoice_id.invoice_date, invoice_id.amount_total)
            main_content = {
                'subject': _('Payment Received: %s') % invoice_id.payment_reference,
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': invoice_id.partner_id.email,
            }
            self.env['mail.mail'].create(main_content).send()
        return res
