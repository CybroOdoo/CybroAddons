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
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    so_approval = fields.Boolean(string="Sale Order Approval")
    so_min_amount = fields.Monetary(string="Minimum Amount")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['so_approval'] = self.env['ir.config_parameter'].sudo().get_param(
            "sales_order_double_approval.so_approval", default="")
        res['so_min_amount'] = self.env['ir.config_parameter'].sudo().get_param(
            "sales_order_double_approval.so_min_amount", default="")
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].set_param("sales_order_double_approval.so_approval",
                                                  self.so_approval or '')
        self.env['ir.config_parameter'].set_param("sales_order_double_approval.so_min_amount",
                                                  self.so_min_amount or '')
        super(ResConfigSettings, self).set_values()
