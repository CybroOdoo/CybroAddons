# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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
from odoo import fields, models, _
from odoo import exceptions


class PurchaseOrder(models.Model):
    """ Inheriting the purchase order model to add the fields and direct send
    the email button"""
    _inherit = 'purchase.order'
    _description = 'purchase order'

    direct_send_rfq = fields.Boolean(
        "Direct Send Request for Quotation",
        help="Direct Send Request for Quotation by Mail.")
    direct_send_po = fields.Boolean(
        "Direct Send Purchase Order",
        help="Direct Send Purchase Order by Mail.")

    def direct_send_purchase(self):
        """Sending a direct send purchase email to the customer."""
        is_direct_send_email_purchase = self.env[
            'ir.config_parameter'].sudo().get_param(
            'direct_send_email_template.is_direct_send_email_purchase')
        if is_direct_send_email_purchase:
            purchase_state = {
                'draft': {
                    'template_key': 'direct_send_mailtemplate_prfq',
                    'field_key': 'direct_send_rfq',
                    'error_msg': _("Template not defined for Request for Quotation."),
                },
                'purchase': {
                    'template_key': 'direct_send_mailtemplate_po',
                    'field_key': 'direct_send_po',
                    'error_msg': _("Template not defined For Purchase Order."),
                },
            }
            if self.state in purchase_state:
                template = int(self.env['ir.config_parameter'].sudo().get_param(
                    'direct_send_email_template.' + purchase_state[self.state]['template_key']))
                if template:
                    template_id = self.env['mail.template'].browse(template)
                    self.with_context(force_send=True).message_post_with_source(template_id)
                    self.write({purchase_state[self.state]['field_key']: True})
                else:
                    raise exceptions.ValidationError(purchase_state[self.state]['error_msg'])
        else:
            raise exceptions.ValidationError(
                _("Not Configured Direct Send Email Setting")

            )
