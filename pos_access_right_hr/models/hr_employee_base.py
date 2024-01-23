# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class HrEmployeeBase(models.AbstractModel):
    """The inherited class HrEmployee to add new fields to 'hr.employee' """
    _inherit = "hr.employee.base"

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
        string="POS-Disable price",
        help="Disable the %Price button on the POS")
    disable_remove_button = fields.Boolean(
        string="POS-Disable Remove Button",
        help="Disable the back button on the POS")
