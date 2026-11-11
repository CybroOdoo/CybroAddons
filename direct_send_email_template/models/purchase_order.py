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
from odoo import fields, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    """Inherit purchase.order to add direct send email functionality."""

    _inherit = 'purchase.order'

    direct_send_rfq = fields.Boolean(
        string="Direct Send Request for Quotation",
        help="Directly send request for quotation by email.",
    )
    direct_send_po = fields.Boolean(
        string="Direct Send Purchase Order",
        help="Directly send purchase order by email.",
    )

    def action_direct_send_purchase(self):
        """Send direct purchase email to vendor."""
        config_param = self.env['ir.config_parameter'].sudo()
        is_direct_send_email_purchase = config_param.get_bool(
            'direct_send_email_template.is_direct_send_email_purchase',
        )
        if is_direct_send_email_purchase:
            purchase_state = {
                'draft': {
                    'template_key': 'direct_send_email_template.direct_send_mailtemplate_prfq',
                    'field_key': 'direct_send_rfq',
                    'error_msg': self.env._("Email template is not configured for Requests for Quotation."),
                },
                'purchase': {
                    'template_key': 'direct_send_email_template.direct_send_mailtemplate_po',
                    'field_key': 'direct_send_po',
                    'error_msg': self.env._("Email template is not configured for Purchase Orders."),
                },
            }
            if self.state in purchase_state:
                template_id = config_param.get_int(purchase_state[self.state]['template_key'])
                if template_id:
                    template = self.env['mail.template'].browse(template_id)
                    self.with_context(force_send=True).message_post_with_source(template)
                    self.write({purchase_state[self.state]['field_key']: True})
                else:
                    raise ValidationError(purchase_state[self.state]['error_msg'])
        else:
            raise ValidationError(
                self.env._("Direct Send Email is not enabled in the settings."),
            )
