# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj @cybrosys(odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit re.config.settings to add more fields"""
    _inherit = 'res.config.settings'

    is_show_digital_sign_po = fields.Boolean(
        config_parameter='digital_signature.is_show_digital_sign_po',
        help="Show digital signature for purchase orders.")
    is_enable_options_po = fields.Boolean(
        config_parameter='digital_signature.is_enable_options_po',
        help="Enable options for digital signatures on purchase orders.")
    is_confirm_sign_po = fields.Boolean(
        config_parameter='digital_signature.is_confirm_sign_po',
        help="Require confirmation for digital signatures on purchase orders.")
    is_show_digital_sign_inventory = fields.Boolean(
        config_parameter='digital_signature.is_show_digital_sign_inventory',
        help="Show digital signature for inventory operations.")
    is_enable_options_inventory = fields.Boolean(
        config_parameter='digital_signature.is_enable_options_inventory',
        help="Enable options for digital signatures on inventory operations.")
    sign_applicable = fields.Selection(
        [('picking_operations', 'Picking Operations'),
         ('delivery', 'Delivery Slip'), ('both', 'Both')],
        string="Sign Applicable inside", default="picking_operations",
        config_parameter='digital_signature.sign_applicable',
        help="Define where the digital signature is applicable.")
    is_confirm_sign_inventory = fields.Boolean(
        config_parameter='digital_signature.is_confirm_sign_inventory',
        help="Require confirmation for digital signatures on inventory "
             "operations.")
    is_show_digital_sign_invoice = fields.Boolean(
        config_parameter='digital_signature.is_show_digital_sign_invoice',
        help="Show digital signature for invoices.")
    is_enable_options_invoice = fields.Boolean(
        config_parameter='digital_signature.is_enable_options_invoice',
        help="Enable options for digital signatures on invoices.")
    is_confirm_sign_invoice = fields.Boolean(
        config_parameter='digital_signature.is_confirm_sign_invoice',
        help="Require confirmation for digital signatures on invoices.")
    is_show_digital_sign_bill = fields.Boolean(
        config_parameter='digital_signature.is_show_digital_sign_bill',
        help="Show digital signature for bills.")
