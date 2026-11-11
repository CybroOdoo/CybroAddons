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


class AccountMove(models.Model):
    """Inherit account.move to add direct send email functionality."""

    _inherit = 'account.move'

    direct_send_inv = fields.Boolean(
        string="Direct Send Invoice",
        help="Directly send customer invoice by email.",
    )
    direct_send_crd = fields.Boolean(
        string="Direct Send Credit Note",
        help="Directly send customer credit note by email.",
    )
    direct_send_bill = fields.Boolean(
        string="Direct Send Vendor Bill",
        help="Directly send vendor bill by email.",
    )
    direct_send_ref = fields.Boolean(
        string="Direct Send Vendor Refund",
        help="Directly send vendor refund by email.",
    )

    def action_direct_send_account(self):
        """Send direct account email to customer or vendor."""
        config_param = self.env['ir.config_parameter'].sudo()
        is_direct_send_email_account = config_param.get_bool(
            'direct_send_email_template.is_direct_send_email_account',
        )
        if is_direct_send_email_account:
            move_type = {
                'out_invoice': {
                    'template_key': 'direct_send_email_template.direct_send_mailtemplate_inv',
                    'field_key': 'direct_send_inv',
                    'error_msg': self.env._("Email template is not configured for Customer Invoices."),
                },
                'out_refund': {
                    'template_key': 'direct_send_email_template.direct_send_mailtemplate_credit',
                    'field_key': 'direct_send_crd',
                    'error_msg': self.env._("Email template is not configured for Customer Credit Notes."),
                },
                'in_invoice': {
                    'template_key': 'direct_send_email_template.direct_send_mailtemplate_bill',
                    'field_key': 'direct_send_bill',
                    'error_msg': self.env._("Email template is not configured for Vendor Bills."),
                },
                'in_refund': {
                    'template_key': 'direct_send_email_template.direct_send_mailtemplate_refund',
                    'field_key': 'direct_send_ref',
                    'error_msg': self.env._("Email template is not configured for Vendor Refunds."),
                },
            }
            if self.state == 'posted' and self.move_type in move_type:
                template_id = config_param.get_int(move_type[self.move_type]['template_key'])
                if template_id:
                    template = self.env['mail.template'].browse(template_id)
                    self.with_context(force_send=True).message_post_with_source(template)
                    self.write({move_type[self.move_type]['field_key']: True})
                else:
                    raise ValidationError(move_type[self.move_type]['error_msg'])
        else:
            raise ValidationError(
                self.env._("Direct Send Email is not enabled in the settings."),
            )
