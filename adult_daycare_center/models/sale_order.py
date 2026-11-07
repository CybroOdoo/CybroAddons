# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
##########################################################################
from odoo import Command, api, fields, models


class SaleOrder(models.Model):
    """Extend sale orders with daycare-related information."""
    _inherit = 'sale.order'

    adult_person_id = fields.Many2one('res.partner', domain="[('is_adult_member', '=', True)]",
                                      help="Adult person name")

    @api.onchange('adult_person_id')
    def _onchange_adult_person_id(self):
        """Load the activities of the chosen adult person into the order
        lines, replacing any existing lines."""
        products = self.adult_person_id.daycare_activities_ids.product_id\
            .product_variant_id
        self.order_line = [Command.clear()] + [
            Command.create({'product_id': product.id, 'product_uom_qty': 1})
            for product in products
        ]
