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
from odoo import fields, models, api


class ProductSupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    discount = fields.Float(string="Discount (%)")
    _sql_constraints = [
        (
            "maximum_discount",
            "CHECK (discount <= 100.0)",
            "Discount must be lower than 100%.",
        )
    ]

    @api.onchange("name")
    def default_discount(self):
        for supplier in self.filtered("name"):
            supplier.write({'discount': supplier.name.default_discount})
