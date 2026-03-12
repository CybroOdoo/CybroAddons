# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """ Inheriting the settings to add custom fields """
    _inherit = 'res.config.settings'

    so_approval = fields.Boolean(
        string="Sale Order Approval",
        help="Enable this option to require double validation for sale orders. "
             "When enabled, sale orders exceeding the specified minimum amount "
             "will require approval by a sales manager."
    )
    so_min_amount = fields.Monetary(
        string="Minimum Amount",
        help="Specify the minimum amount that triggers the double validation "
             "for sale orders. Sale orders exceeding this amount will require "
             "approval by a sales manager."
    )

    @api.model
    def get_values(self):
        """ Override to get the values of the custom fields from the
        'ir.config_parameter' model. """
        res = super(ResConfigSettings, self).get_values()
        res['so_approval'] = self.env['ir.config_parameter'].sudo().get_param(
            "sales_order_double_approval.so_approval", default="")
        res['so_min_amount'] = self.env['ir.config_parameter'].sudo().get_param(
            "sales_order_double_approval.so_min_amount", default="")
        return res

    @api.model
    def set_values(self):
        """ Override to set the values of the custom fields in the
        'ir.config_parameter' model. """
        self.env['ir.config_parameter'].set_param(
            "sales_order_double_approval.so_approval",
            self.so_approval or '')
        self.env['ir.config_parameter'].set_param(
            "sales_order_double_approval.so_min_amount",
            self.so_min_amount or '')
        super(ResConfigSettings, self).set_values()
