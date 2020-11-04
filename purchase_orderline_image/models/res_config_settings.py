# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models,api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    show_product_image_in_report_purchase = fields.Boolean(string="Show Product Image", default=False)

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('purchase_orderline_image.show_product_image_in_report_purchase',
                                                         self.show_product_image_in_report_purchase)
        res = super(ResConfigSettings, self).set_values()
        return res

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param = self.env['ir.config_parameter'].sudo().get_param(
            'purchase_orderline_image.show_product_image_in_report_purchase',
            self.show_product_image_in_report_purchase)
        res.update(
            show_product_image_in_report_purchase=param
        )
        return res
