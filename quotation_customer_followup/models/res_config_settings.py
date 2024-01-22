# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class ConfigurationSettings(models.TransientModel):
    """Class for adding new fields in the settings"""
    _inherit = "res.config.settings"

    mail_template_id = fields.Many2one(comodel_name='mail.template',
                                       string='Mail Template',
                                       config_parameter
                                       ="res.config.settings.mail_template",
                                       help='Select a template for the email '
                                            'to be sent for the followup mail.')
    expiry_mail_id = fields.Many2one(comodel_name='mail.template',
                                     string='Expiry Mail Template',
                                     config_parameter
                                     ="res.config.settings.expiry_mail_template",
                                     help='Select a template for the email to '
                                          'be sent for the expiry mail.')
    quotation_followup_mail = fields.Boolean(
        config_parameter="res.config.settings.followup_enable",
        string='Quotation Followup By Email',
        help='Enable to make a quotation followup email')
    quotation_expiry_mail = fields.Boolean(
        config_parameter="res.config.settings.expiry_enable",
        help='Enable to make a quotation expiry email')
    days = fields.Integer(string='days',
                          config_parameter="res.config.settings.days",
                          help='Select number of days that the email should '
                               'send after')
    expiry_days = fields.Integer(
        string='Expiry Days',
        config_parameter="res.config.settings.expiry_days",
        help='Select number of days that to set the expiry date as default '
             'for quotation')
