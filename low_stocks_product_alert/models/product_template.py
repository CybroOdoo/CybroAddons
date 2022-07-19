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


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'product template'

    alert_state = fields.Boolean(string='Product Alert State', default=False,
                                 compute='_compute_alert_state')
    color_field = fields.Char(string='Background color')

    @api.depends('qty_available')
    def _compute_alert_state(self):
        is_low_stock_alert = self.env[
            'ir.config_parameter'].sudo().get_param(
            'low_stocks_product_alert.is_low_stock_alert')
        min_low_stock_alert = self.env[
            'ir.config_parameter'].sudo().get_param(
            'low_stocks_product_alert.min_low_stock_alert')
        if is_low_stock_alert:
            for rec in self:
                rec.alert_state = False
                rec.color_field = 'white'
                if rec.type == 'product':
                    if rec.qty_available <= int(min_low_stock_alert):
                        rec.alert_state = True
                        rec.color_field = '#fdc6c673'

        else:
            self.alert_state = False
            self.color_field = 'white'

