# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen(odoo@cybrosys.com)
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
from odoo import fields, models


class DiscountSaleReport(models.Model):
    """This class inherits 'sale.report' and adds field discount"""
    _inherit = 'sale.report'

    discount = fields.Float('Discount', readonly=True,
                            help="Specify the discount amount.")

    def _select(self):
        """It extends the behavior of a method in the class by adding a
         new column, discount, to the SQL query. This new column represents
         the total discount for sales transactions, calculated based on
         various factors and values related to the sale. """
        res = super(DiscountSaleReport, self)._select()
        select_str = res + """,sum(l.product_uom_qty / u.factor * u2.factor * cr.rate * l.price_unit * l.discount / 100.0)
         as discount"""
        return select_str
