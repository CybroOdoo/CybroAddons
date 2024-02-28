# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya Babu (odoo@cybrosys.com)
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
##############################################################################
from odoo import fields, models


class LoyaltyCard(models.Model):
    """This class extends the 'loyalty.card' model to
    add a wallet_amount function for transferring loyalty
    points between partners."""
    _inherit = 'loyalty.card'

    def wallet_amount(self, args):
        """Transfer an amount from one customer's wallet to another."""
        recipient = self.env['res.partner'].sudo().search(
            [('phone', '=', args.get('number'))])
        recipient_wallet = self.search([('partner_id', '=', recipient.id)])

        payer_wallet = self.search(
            [('partner_id', '=', self.env.user.partner_id.id)])

        if recipient_wallet and int(args.get('amount')) <= payer_wallet.points:
            recipient_wallet.update(
                {'points': recipient_wallet.points + int(args.get('amount'))})

            payer_wallet.update(
                {'points': payer_wallet.points - int(args.get('amount'))})

            recipient_name = recipient.name
            recipient_wallet_points = recipient_wallet.points
            partner_name = self.env.user.partner_id.name

            body = f'<p>Mr {recipient_name},<br>' \
                   f'Amount is added from {partner_name}. ' \
                   f'Current balance is {recipient_wallet_points}.</p>'

            mail_template = self.env.ref(
                'website_customer_wallet.transfer_email_template')
            mail_template.sudo().write({
                'email_to': recipient.email,
                'body_html': body
            })
            mail_template.send_mail(self.id, force_send=True)

            self.env['customer.wallet.transaction'].create({
                'date': fields.Date.today(),
                'partner_id': self.env.user.partner_id.id,
                'amount_type': 'transfer',
                'amount': int(args.get('amount'))
            })

            values = {
                'payer_current_balance': payer_wallet.points,
                'recipient_current_balance': recipient_wallet.points
            }
            return values
        else:
            return False
