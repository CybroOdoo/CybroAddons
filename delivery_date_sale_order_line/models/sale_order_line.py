# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class SaleOrderLine(models.Model):
    """Inheriting sale order line"""
    _inherit = 'sale.order.line'

    delivery_datetime = fields.Datetime(string='Delivery Date',
                                        help='Delivery date for the product')

    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be
        created from a stock rule coming from a sale order line. Here added
        delivery_datetime custom key in to move.
        """
        res = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        res['delivery_datetime'] = self.delivery_datetime
        if self.delivery_datetime:
            res['date_planned'] = self.delivery_datetime
        return res
