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


class SaleOrder(models.Model):
    """ inheriting the sale order model to add the fields and direct send the email button"""
    _inherit = 'sale.order'

    direct_send_quo = fields.Boolean(
        "Direct Send Quotation", help="Direct Send Quotation by Mail")
    direct_send_so = fields.Boolean(
        "Direct Send sale Order", help="Direct Send Sale Order by Mail")

    def direct_send_sale(self):
        """Sending a direct send sales email to the customer."""
        is_direct_send_email_sale = self.env[
            'ir.config_parameter'].sudo().get_param(
            'direct_send_email_template.is_direct_send_email_sale')
        if is_direct_send_email_sale:
            sale_state = {
                'draft': {
                    'template_key': 'direct_send_mailtemplate_sq_id',
                    'field_key': 'direct_send_quo',
                    'error_msg': _("Template not defined for Sale Order Quotation."),
                },
                'sale': {
                    'template_key': 'direct_send_mailtemplate_so_id',
                    'field_key': 'direct_send_so',
                    'error_msg': _("Template not defined for Sale Order Confirmation."),
                },
            }
            if self.state in sale_state:
                template = int(self.env['ir.config_parameter'].sudo().get_param(
                    'direct_send_email_template.' + sale_state[self.state]['template_key']))
                if template:
                    template_id = self.env['mail.template'].browse(template)
                    self.with_context(force_send=True).message_post_with_template(
                        template_id.id, email_layout_xmlid='mail.mail_notification_light')
                    self.write({sale_state[self.state]['field_key']: True})
                else:
                    raise ValidationError(sale_state[self.state]['error_msg'])
        else:
            raise ValidationError(
                _("Not Configured Direct Send Email Setting"))
