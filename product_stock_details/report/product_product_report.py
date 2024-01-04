# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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
from odoo import api, models


class ProductStockDetails(models.AbstractModel):
    """Created Abstract model for report on Product Stock Details"""
    _name = 'report.product_stock_details.report_product_stock_template'
    _description = "Product Stock Details Report"

    @api.model
    def _get_report_values(self, docids, data):
        """Method for getting report values."""
        docs = self.env.context.get('active_ids')
        if docs is None:
            docs = docids
        return {
            'data': self.env['product.product'].search([('id', 'in', docs)])
        }
