# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
from odoo import models


class PosConfig(models.Model):
    """Inheriting pos config to get location summary"""
    _inherit = 'pos.config'

    def get_location_summary(self, location_id):
        """Function to get location details"""
        location_quant = self.env['stock.quant'].search(
            [('location_id', '=', int(location_id))])
        for quant in location_quant.filtered(
                lambda x: x.product_id.available_in_pos):
            location_summary = [
                {
                    'product_id': quant.product_id.id,
                    'product': quant.product_id.name,
                    'quantity': quant.available_quantity,
                }
            ]
            return location_summary
