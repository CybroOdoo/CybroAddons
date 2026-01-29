# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api, _


class ResConfigurationInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    show_digital_sign_po = fields.Boolean(config_parameter='digital_signature.show_digital_sign_po')
    enable_options_po = fields.Boolean(default=True, config_parameter='digital_signature.enable_options_po')
    confirm_sign_po = fields.Boolean(config_parameter='digital_signature.confirm_sign_po')
    show_digital_sign_inventory = fields.Boolean(config_parameter='digital_signature.show_digital_sign_inventory')
    enable_options_inventory = fields.Boolean(default=True, config_parameter='digital_signature.enable_options_inventory')
    sign_applicable = fields.Selection([
        ('picking_operations', 'Picking Operations'),
        ('delivery', 'Delivery Slip'),
        ('both', 'Both'),
    ], string="Sign Applicable inside",
        default="picking_operations",
        config_parameter='digital_signature.sign_applicable')
    confirm_sign_inventory = fields.Boolean(config_parameter='digital_signature.confirm_sign_inventory')
    show_digital_sign_invoice = fields.Boolean(config_parameter='digital_signature.show_digital_sign_invoice')
    enable_options_invoice = fields.Boolean(config_parameter='digital_signature.enable_options_invoice')
    confirm_sign_invoice = fields.Boolean(config_parameter='digital_signature.confirm_sign_invoice')
    show_digital_sign_bill = fields.Boolean(config_parameter='digital_signature.show_digital_sign_bill')

