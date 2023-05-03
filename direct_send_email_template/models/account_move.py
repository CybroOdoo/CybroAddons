# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import ValidationError
from odoo import fields, models, _


class AccountMove(models.Model):
    """ inheriting the account model to add the fields and direct send the email button"""
    _inherit = 'account.move'

    direct_send_inv = fields.Boolean(
        "Direct Send Invoice", help="Direct Send Customer Invoice by Mail")
    direct_send_crd = fields.Boolean(
        "Direct Send Credit Note", help="Direct Send Credit Note by Mail")
    direct_send_bill = fields.Boolean(
        "Direct Send Bill", help="Direct Send Vendor Bill by Mail ")
    direct_send_ref = fields.Boolean(
        "Direct Send Refund", help="Direct Send Refund by Mail")

    def direct_send_account(self):
        """Sending a direct send accounts email to the customer."""
        is_direct_send_email_account = self.env[
            'ir.config_parameter'].sudo().get_param(
            'direct_send_email_template.is_direct_send_email_account')
        if is_direct_send_email_account:
            move_type = {
                'out_invoice': {
                    'template_key': 'direct_send_mailtemplate_inv_id',
                    'field_key': 'direct_send_inv',
                    'error_msg': _("Template not defined for Customer Invoice."),
                },
                'out_refund': {
                    'template_key': 'direct_send_mailtemplate_credit_id',
                    'field_key': 'direct_send_crd',
                    'error_msg': _("Template not defined for Customer Credit Note."),
                },
                'in_invoice': {
                    'template_key': 'direct_send_mailtemplate_bill_id',
                    'field_key': 'direct_send_bill',
                    'error_msg': _("Template not defined for Vendor Bill."),
                },
                'in_refund': {
                    'template_key': 'direct_send_mailtemplate_refund_id',
                    'field_key': 'direct_send_ref',
                    'error_msg': _("Template not defined for Vendor Credit Note."),
                }
            }
            if self.state == 'posted':
                if self.move_type in move_type:
                    template = int(self.env['ir.config_parameter'].sudo().get_param(
                        'direct_send_email_template.' + move_type[self.move_type]['template_key']))
                    if template:
                        template_id = self.env['mail.template'].browse(template)
                        self.with_context(force_send=True).message_post_with_template(
                            template_id.id, email_layout_xmlid='mail.mail_notification_light')
                        self.write({move_type[self.move_type]['field_key']: True})
                    else:
                        raise ValidationError(move_type[self.move_type]['error_msg'])
        else:
            raise ValidationError(_("Not Configured Direct Send Email Setting"))
