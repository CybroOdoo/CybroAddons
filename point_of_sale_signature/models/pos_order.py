# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Noorjahan @ cybrosys,(odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models

class PosOrder(models.Model):
    """To add the customer signature field in pos order"""
    _inherit = "pos.order"

    customer_signature = fields.Binary(string="Customer Signature", attachment=True,
                                       help="Adding the customer signature in POS order")

    @api.model
    def _order_fields(self, ui_order):
        """Allow POS custom fields"""
        vals = super()._order_fields(ui_order)
        vals["customer_signature"] = ui_order.get("customer_signature")
        return vals
