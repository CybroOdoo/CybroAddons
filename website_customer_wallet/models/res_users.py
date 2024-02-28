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
from odoo import models, fields


class ResUsers(models.Model):
    """Inherited and added the pin number and aded function for change the
     pin-number."""
    _inherit = 'res.users'

    pin_number = fields.Integer(string='PIN Number',
                                help='PIN Number of the users.')

    def change_pin(self, kw):
        """Reset the pin."""
        if not self.env.user.pin_number == int(kw.get('current_pswd')):
            return True
        else:
            self.env.user.write({'pin_number': int(kw.get('new_pswd'))})
            recipient = self.env.user.partner_id
            recipient_name = recipient.name
            body = '<p>Mr ' + str(
                recipient_name) + ',<br>' 'Your Wallet PIN is Changed. ' '.</p>'
            mail_template = self.env.ref(
                'website_customer_wallet.wallet_change_pin_template')
            mail_template.sudo().write({
                'email_to': recipient.email,
                'body_html': body
            })
            mail_template.send_mail(self.id, force_send=True)
            return False
