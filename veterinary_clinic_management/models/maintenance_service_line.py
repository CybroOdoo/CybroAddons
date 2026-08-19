# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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


class MaintenanceServiceLine(models.Model):
    """
        Model to store maintenance service details in veterinary clinic management.
    """
    _name = "maintenance.service.line"
    _description = "Maintenance Service Line"

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        help="Product used for the maintenance service.", required=True
    )
    description = fields.Char(
        string="Description",
        related="product_id.name",
        help="Description of the product used."
    )
    quantity = fields.Integer(
        string="Quantity",
        default=1,
        help="Quantity of the product used for the maintenance."
    )
    unit_price = fields.Float(
        string="Unit Price",
        related="product_id.list_price",
        help="Unit price of the product used."
    )
    subtotal = fields.Monetary(
        string="SubTotal",
        compute="_compute_subtotal",
        help="Total cost for the quantity of products used in maintenance."
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.company.currency_id.id,
        help="Currency used for the subtotal."
    )
    maintenance_id = fields.Many2one(
        string="Maintenance Id",
        comodel_name="res.maintenance",
        help="Maintenance record associated with this service line."
    )

    @api.depends("quantity", "unit_price")
    def _compute_subtotal(self):
        """
        Compute the subtotal based on the quantity and unit price of the product.
        """
        for record in self:
            record.subtotal = record.quantity * record.unit_price