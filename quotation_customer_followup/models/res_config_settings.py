# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """This model was inherited to add a field mail template, follow-up days"""

    _inherit = "res.config.settings"

    mail_template_id = fields.Many2one(
        'mail.template',
        string='Mail Template',
        help="Choose Mail Template for customer follow up",
        config_parameter
        ="quotation_customer_followup.mail_template")
    expiry_mail_id = fields.Many2one(
        'mail.template',
        string='Expiry Mail Template',
        help="Choose Mail Template for Expiry Date Reminder Mail",
        config_parameter=
        "quotation_customer_followup.expiry_mail_template")
    quotation_followup_mail = fields.Boolean(
        config_parameter=
        "quotation_customer_followup.followup_enable",
        help="Option for Quotation Followup By Email",
        string='Quotation Followup By Email')
    quotation_expiry_mail = fields.Boolean(
        string="Quotation Expiry Mail",
        help="Option for Quotation Expiry Mail",
        config_parameter="quotation_customer_followup.expiry_enable")
    days = fields.Integer(
        string='Days',
        help="Choose days, From Which Follow up mail will send",
        config_parameter="quotation_customer_followup.days")
    expiry_days = fields.Integer(
        string='Expiry Days',
        help="Choose days, from which Expiry Mail will Send",
        config_parameter="quotation_customer_followup.expiry_days")
