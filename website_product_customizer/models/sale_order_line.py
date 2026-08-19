# -- coding: utf-8 --
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """Extends sale.order.line to link design customizations."""
    _inherit = 'sale.order.line'
    _description = 'Sale Order Line'

    design_customization_id = fields.Many2one(
        'product.design.customization',
        string="Design Customization",
        help="Link to the customer's design customization record. "
             "Contains the full design data (text, images, positions) for this order line."
    )
    is_designed = fields.Boolean(
        string="Is Designed",
        compute='_compute_is_designed',
        store=True,
        help="Indicates whether this order line has an attached custom design."
    )


    @api.depends('design_customization_id')
    def _compute_is_designed(self):
        """Set whether the order line has a design customization."""
        for line in self:
            line.is_designed = bool(line.design_customization_id)
