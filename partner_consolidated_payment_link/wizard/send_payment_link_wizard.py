# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1). It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included in
#    all copies or substantial portions of the Software.
#
#############################################################################

from odoo import fields, models, _
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
        default=lambda self: self.env.context.get('active_id'),
        help="Customer for whom the payment link will be sent."
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
