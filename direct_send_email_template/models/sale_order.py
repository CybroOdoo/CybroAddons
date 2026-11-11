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


class SaleOrder(models.Model):
    """Inherit sale.order to add direct send email functionality."""

    _inherit = 'sale.order'

    direct_send_quo = fields.Boolean(
        string="Direct Send Quotation",
        help="Directly send quotation by email.",
    )
    direct_send_so = fields.Boolean(
        string="Direct Send Sales Order",
        help="Directly send sales order by email.",
    )

    def action_direct_send_sale(self):
        """Send direct sales email to customer."""
        config_param = self.env['ir.config_parameter'].sudo()
        is_direct_send_email_sale = config_param.get_bool(
            'direct_send_email_template.is_direct_send_email_sale',
        )
        if is_direct_send_email_sale:
            sale_state = {
                'draft': {
                    'template_key': 'direct_send_email_template.direct_send_mailtemplate_sq',
                    'field_key': 'direct_send_quo',
                    'error_msg': self.env._("Email template is not configured for Quotations."),
                },
                'sale': {
                    'template_key': 'direct_send_email_template.direct_send_mailtemplate_so',
                    'field_key': 'direct_send_so',
                    'error_msg': self.env._("Email template is not configured for Sales Orders."),
                },
            }
            if self.state in sale_state:
                template_id = config_param.get_int(sale_state[self.state]['template_key'])
                if template_id:
                    template = self.env['mail.template'].browse(template_id)
                    self.with_context(force_send=True).message_post_with_source(template)
                    self.write({sale_state[self.state]['field_key']: True})
                else:
                    raise ValidationError(sale_state[self.state]['error_msg'])
        else:
            raise ValidationError(
                self.env._("Direct Send Email is not enabled in the settings."),
            )
