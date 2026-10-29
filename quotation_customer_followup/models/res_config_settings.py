# -*- coding: utf-8 -*-
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


class ConfigurationSettings(models.TransientModel):
    """Class for adding new fields in the settings"""
    _inherit = "res.config.settings"

    mail_template_id = fields.Many2one(
        comodel_name='mail.template',
        string='Mail Template',
        config_parameter="quotation_customer_followup.mail_template",
        help='Select a template for the email to be sent for the follow-up mail.',
    )
    expiry_mail_id = fields.Many2one(
        comodel_name='mail.template',
        string='Expiry Mail Template',
        config_parameter="quotation_customer_followup.expiry_mail_template",
        help='Select a template for the email to be sent for the expiry mail.',
    )
    quotation_followup_mail = fields.Boolean(
        string='Quotation Follow-up By Email',
        config_parameter="quotation_customer_followup.followup_enable",
        help='Enable to send quotation follow-up emails.',
    )
    quotation_expiry_mail = fields.Boolean(
        string='Quotation Expiry Mail',
        config_parameter="quotation_customer_followup.expiry_enable",
        help='Enable to make a quotation expiry email',
    )
    days = fields.Integer(
        string='Days',
        config_parameter="quotation_customer_followup.days",
        help='Select number of days after which the follow-up email should be sent.',
    )
    expiry_days = fields.Integer(
        string='Expiry Days',
        config_parameter="quotation_customer_followup.expiry_days",
        help='Select number of days to set as the default expiry date for quotations.',
    )

