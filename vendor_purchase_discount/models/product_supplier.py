# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ajmunnisa KP (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class ProductSupplierInfo(models.Model):
    """Inherits the model to include function to update the discount when
    partner id is changed."""
    _inherit = "product.supplierinfo"

    discount = fields.Float(string="Discount (%)", help="Discount for the "
                                                        "supplier in "
                                                        "percentage")
    _sql_constraints = [
        (
            "maximum_discount",
            "CHECK (discount <= 100.0)",
            "Discount must be lower than 100%.",
        )
    ]

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """Updates discount when partner id is changed. """
        for supplier in self.filtered("partner_id"):
            supplier.write({'discount': supplier.partner_id.default_discount})
