# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nubla Sherin k (<https://www.cybrosys.com>)
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
################################################################################
from odoo import http
from odoo.http import request
import json

class CustomReceipt(http.Controller):

    @http.route('/my/receipt/<int:order_id>', type='http', auth='public')
    def my_receipt(self, order_id, t=None):
        order = request.env['pos.order'].sudo().browse(order_id)

        if not order or order.custom_receipt_token != t:
            return "Invalid receipt"

        config = order.session_id.config_id
        fields = []

        if config.selected_product_fields:
            fields = json.loads(config.selected_product_fields)

        return request.render("pos_receipt_ui_customizer.custom_pos_receipt", {
            "order": order,
            "dynamic_fields": fields,
        })

    @http.route('/my/receipt/pdf/<int:order_id>', type='http', auth='public')
    def my_receipt_pdf(self, order_id, t=None):
        order = request.env['pos.order'].sudo().browse(order_id)

        if not order or order.custom_receipt_token != t:
            return "Invalid receipt"

        config = order.session_id.config_id
        fields = []
        if config.selected_product_fields:
            fields = json.loads(config.selected_product_fields)

        lines = []
        sl = 1
        for line in order.lines:
            row = {
                "sl": sl,
                "product": line.product_id.display_name,
                "qty": line.qty,
                "price": "%.2f" % line.price_unit,
                "total": "%.2f" % line.price_subtotal_incl,
            }

            for f in fields:
                row[f] = str(line.product_id[f] or "") if f in line.product_id else ""

            lines.append(row)
            sl += 1

        data = {
            "company_name": order.company_id.name,
            "phone": order.company_id.phone or "",
            "order_name": order.name,
            "date": order.date_order.strftime("%d-%m-%Y %H:%M"),
            "tax": "%.2f" % order.amount_tax,
            "total": "%.2f" % order.amount_total,
            "dynamic_fields": fields,
            "lines": lines,
            "qr": order.custom_qr_image.decode() if order.custom_qr_image else "",
        }

        pdf, _ = request.env["ir.actions.report"].sudo()._render_qweb_pdf(
            request.env.ref("pos_receipt_ui_customizer.action_custom_pos_receipt_pdf"),
            res_ids=[order.id],
            data={"values": data},
        )

        return request.make_response(pdf, [
            ("Content-Type", "application/pdf"),
            ("Content-Disposition", f'attachment; filename="Receipt-{order.name}.pdf"')
        ])