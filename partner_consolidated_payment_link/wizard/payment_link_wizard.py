# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Viswanth K(odoo@cybrosys.com)
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
from odoo import models, fields, _
from odoo.exceptions import UserError


class SendPaymentLinkWizard(models.TransientModel):
    """
    This wizard asks for confirmation before sending a payment link email.
    """
    _name = 'send.payment.link.wizard'
    _description = 'Wizard to Confirm Sending Payment Link'

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        readonly=True,
        default=lambda self: self.env.context.get('active_id')
    )

    def action_send_mail(self):
        """
        This method is called when the 'Send Email' button is clicked.
        It generates a placeholder payment link and sends the email.
        """
        self.ensure_one()

        if not self.partner_id.email:
            raise UserError(_("This customer does not have an email address set."))

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        payment_link = f"{base_url}/payment/balance/{self.partner_id.id}"

        template = self.env.ref('partner_consolidated_payment_link.email_template_payment_link', raise_if_not_found=False)
        if not template:
             raise UserError(_("The email template for the payment link was not found."))

        ctx = dict(self.env.context)
        ctx.update({
            'default_model': 'res.partner',
            'default_res_id': self.partner_id.id,
            'payment_link': payment_link,
        })
        template.with_context(ctx).send_mail(self.partner_id.id, force_send=True)
        return {'type': 'ir.actions.act_window_close'}
