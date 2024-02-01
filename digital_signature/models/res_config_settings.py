# -*- coding: utf-8 -*-
#############################################################################
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited the res config settings for returning the value of digital
       signature and company stamp from settings"""
    _inherit = 'res.config.settings'

    show_digital_sign_po = fields.Boolean(
        config_parameter='digital_signature.show_digital_sign_po',
        help="Enable to show sign in purchase order")
    enable_options_po = fields.Boolean(
        config_parameter='digital_signature.enable_options_po',
        help="Enable to option in purchase order")
    confirm_sign_po = fields.Boolean(
        config_parameter='digital_signature.confirm_sign_po',
        help="Enable to confirm sign in purchase order")
    show_digital_sign_inventory = fields.Boolean(
        config_parameter='digital_signature.show_digital_sign_inventory',
        help="Enable to show sign in inventory")
    enable_options_inventory = fields.Boolean(
        config_parameter='digital_signature.enable_options_inventory',
        help="Enable to option in inventory")
    sign_applicable = fields.Selection([
        ('picking_operations', 'Picking Operations'),
        ('delivery', 'Delivery Slip'), ('both', 'Both'),
    ], string="Sign Applicable inside",
        default="picking_operations",
        config_parameter='digital_signature.sign_applicable',
        help="Options to whether the feature have to available")
    confirm_sign_inventory = fields.Boolean(
        config_parameter='digital_signature.confirm_sign_inventory',
        help="Enable to confirm sign in inventory")
    show_digital_sign_invoice = fields.Boolean(
        config_parameter='digital_signature.show_digital_sign_invoice',
        help="Enable to show sign in invoice")
    enable_options_invoice = fields.Boolean(
        config_parameter='digital_signature.enable_options_invoice',
        help="Enable to option in invoice")
    confirm_sign_invoice = fields.Boolean(
        config_parameter='digital_signature.confirm_sign_invoice',
        help="Enable to confirm sign in inventory"
    )
    show_digital_sign_bill = fields.Boolean(
        config_parameter='digital_signature.show_digital_sign_bill',
        help="Enable to confirm sign in bill")
    show_company_stamp_po = fields.Boolean(
        config_parameter='digital_signature.show_company_stamp_po',
        help="Enable to confirm stamp in purchase order")
    show_company_stamp_inventory = fields.Boolean(
        config_parameter='digital_signature.show_company_stamp_inventory',
        help="Enable to confirm stamp in inventory")
    show_company_stamp_invoice = fields.Boolean(
        config_parameter='digital_signature.show_company_stamp_invoice',
        help="Enable to confirm stamp in invoice")
    show_company_stamp_bill = fields.Boolean(
        config_parameter='digital_signature.show_company_stamp_bill',
        help="Enable to confirm stamp in bill")
    company_stamp_applicable = fields.Selection([
        ('picking_stamp', 'Picking Operations'),
        ('delivery_stamp', 'Delivery Slip'), ('both_stamp', 'Both'),
    ], string="Company Stamp Applicable",
        default="picking_stamp",
        config_parameter='digital_signature.company_stamp_applicable',
        help="Options to whether the feature have to available"
    )
    company_stamp_applicable_invoicing = fields.Selection([
        ('customer_invoice', 'Customer Invoice'),
        ('vendor_bill', 'Vendor Bill'), ('both', 'Both'),
    ], string="Company Stamp Applicable",
        default="customer_invoice",
        config_parameter='digital_signature.company_stamp_applicable_invoicing',
        help="Options to whether the feature have to available")
