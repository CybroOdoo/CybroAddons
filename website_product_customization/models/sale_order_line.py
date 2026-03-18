# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """
    Inheriting the 'sale.order.line' model add the product_design field
    """
    _inherit = 'sale.order.line'

    product_design = fields.Binary(string="Product Design",
                                   help="Binary field to show product design")
    is_customized_product = fields.Boolean(string="Customized Product product",
                                           help="Is it is a customized product or not",
                                           default=False)

    @api.onchange('product_id')
    def _onchange_product_id_set_design(self):
        """Automatically set product design image when product is selected"""
        if self.product_id and not self.product_design:
            self.product_design = self.product_id.image_1920
