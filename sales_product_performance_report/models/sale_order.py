# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
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
from odoo import api, models


class SaleOrder(models.Model):
    """Inherits the sale order model for creating the product performance report"""
    _inherit = 'sale.order'

    @api.model
    def action_product_performance_report(self):
        """
            action for get product performance report
        """
        return {
            'name': 'Product Performance',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'product.performance',
            'target': 'new',
        }

    @api.model
    def action_sales_performance_report(self):
        """
            action for get sales performance report
        """
        return {
            'name': 'Sales Performance',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sales.performance',
            'target': 'new',
        }
