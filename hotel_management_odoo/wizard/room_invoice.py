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
from odoo import fields, models


class PaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection(
        [("delivered", "Regular invoice"), ("percentage", "Down payment (percentage)"),
         ("fixed", "Down payment (fixed amount)")],
        string="Create Invoice",
        default="delivered",
        required=True, )

    def create_invoices(self):
        ctx = self.env.context.copy()
        if self._context.get("active_model") == "room.reservation":
            HotelFolio = self.env["room.reservation"]
            reservation = self.env["room.reservation"].browse(self._context.get("active_ids", []))
            ctx.update(
                {
                    'reservation_id': reservation.id,
                    'active_ids': reservation.sale_order_id.ids,
                    'active_id': reservation.sale_order_id.id,
                }
            )
        return super(PaymentInv, self.with_context(**ctx)).create_invoices()
