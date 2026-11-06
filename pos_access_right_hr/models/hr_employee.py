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
from odoo import api, fields, models


class HrEmployee(models.Model):
    """The inherited class HrEmployee to add new fields to 'hr.employee' """
    _name = 'hr.employee'
    _inherit = ['hr.employee', 'pos.load.mixin']

    disable_payment = fields.Boolean(
        string="POS-Disable Payment",
        help="Disable the payment button on the POS")
    disable_customer = fields.Boolean(
        string="POS-Disable Customer",
        help="Disable the customer selection button on the POS")
    disable_plus_minus = fields.Boolean(
        string="POS-Disable Plus-Minus",
        help="Disable the +/- button on the POS")
    disable_numpad = fields.Boolean(
        string="POS-Disable Numpad",
        help="Disable the number pad on the POS")
    disable_qty = fields.Boolean(
        string="POS-Disable Qty",
        help="Disable the Qty button on the POS")
    disable_discount = fields.Boolean(
        string="POS-Disable Discount",
        help="Disable the %Disc button on the POS")
    disable_price = fields.Boolean(
        string="POS-Disable Price",
        help="Disable the %Price button on the POS")
    disable_remove_button = fields.Boolean(
        string="POS-Disable Remove Button",
        help="Disable the Backspace key on the POS number pad.")

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Adds custom UI control flags to POS configuration data."""
        result = super()._load_pos_data_fields(config_id)
        result += [
            'disable_payment',
            'disable_customer',
            'disable_plus_minus',
            'disable_numpad',
            'disable_qty',
            'disable_discount',
            'disable_price',
            'disable_remove_button',
        ]
        return result
