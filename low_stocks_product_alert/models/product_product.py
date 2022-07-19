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

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    alert_tag = fields.Char(
        string='Product Alert State', compute='_compute_alert_tag')

    @api.depends('qty_available')
    def _compute_alert_tag(self):
        is_low_stock_alert = self.env[
            'ir.config_parameter'].sudo().get_param(
            'low_stocks_product_alert.is_low_stock_alert')
        min_low_stock_alert = self.env[
            'ir.config_parameter'].sudo().get_param(
            'low_stocks_product_alert.min_low_stock_alert')
        if is_low_stock_alert:
            for rec in self:
                rec.alert_tag = False
                if rec.type == 'product':
                    if rec.qty_available <= int(min_low_stock_alert):
                        rec.alert_tag = rec.qty_available

        else:
            self.alert_tag = False




