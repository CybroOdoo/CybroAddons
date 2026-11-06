# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gee Paul Joby (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from odoo import models, fields
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
            raise UserError(self.env._("This customer does not have an email address set."))

        payment_link = self.partner_id._get_consolidated_payment_url()

        template = self.env.ref('partner_consolidated_payment_link.email_template_payment_link', raise_if_not_found=False)
        if not template:
            raise UserError(self.env._("The email template for the payment link was not found."))

        template.with_context(
            default_model='res.partner',
            default_res_id=self.partner_id.id,
            payment_link=payment_link,
        ).send_mail(self.partner_id.id, force_send=True)
        return {'type': 'ir.actions.act_window_close'}
