###############################################################################
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
###############################################################################
from odoo import api, fields, models


class PosOrder(models.Model):
    """Inherited pos order to add barcode and return tracking fields."""

    _inherit = "pos.order"

    barcode = fields.Char(
        readonly=True,
        help="To get barcode number of this particular order",
    )
    is_return = fields.Boolean(
        string="Return orders",
        default=False,
        help="Differentiate the POS order and return/refund order",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override the create function to add barcode number in order."""
        orders = super().create(vals_list)
        for order in orders:
            if order.pos_reference:
                order.barcode = (
                    order.pos_reference.replace("Order", "")
                    .replace(" ", "")
                    .replace("-", "")
                )
        return orders

    def action_barcode_return(self, barcode):
        """Search the POS order based on the barcode passed from JS and return tracking number."""
        order = self.env["pos.order"].search([("barcode", "=", barcode)])
        if order and order.refund_orders_count == 0:
            return order.tracking_number
        return None

    def _prepare_refund_values(self, current_session):
        """Override this function to mark the order as return."""
        res = super()._prepare_refund_values(current_session)
        res.update({
            "is_return": True,
        })
        return res
