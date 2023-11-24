# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arjun S(odoo@cybrosys.com)
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
"""
With this module user can automatically create the lots when purchasing the
product with tracking in lots, the lots will be created automatically when
confirming the purchase order
"""
from odoo import fields, models


class CustomStockLot(models.Model):
    """
    Creates the model Custom Stock Lot, which contains the name of the lot to be
    created.
    """
    _name = 'custom.stock.lot'
    _description = 'Custom Stock Lot'

    name = fields.Char(string="Name", help="Name of the lot to purchase")
    line_id = fields.Many2one('purchase.order.line', string="Order id",
                              help="Lot ID of the order line")
