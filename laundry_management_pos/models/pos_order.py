# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import _, api, fields, models


class PosOrder(models.Model):
    """ This class is inherited for model pos_order.
                It contains fields and the functions for the model
            Methods:
                create_from_ui(self, orders, draft=False):
                    Supering the create_from_ui that create and update Orders
                    from the frontend PoS application line for the model.

                _prepare_invoice_lines(self):
                    Action perform to create Invoice for the corresponding POS order

    """
    _inherit = "pos.order"

    orderline_washing_type = fields.Boolean(
        string='Washing Type in orderline',
        related='session_id.config_id.orderline_washing_type',
        help='Related to the type in the pos session washing type id')
    laundry_order = fields.Boolean('Laundry',
                                   help='Field for calling the invoice'
                                        ' functionality')

    @api.model
    def _process_order(self, order, existing_order):
        """Normalize result to pos.order recordset and create laundry order if needed"""
        result = super()._process_order(order, existing_order)

        # 🔐 Normalize result to pos.order recordset
        if isinstance(result, int):
            pos_order = self.browse(result)
        else:
            pos_order = result

        if pos_order and pos_order.exists():
            if self._is_laundry_order(pos_order):
                self._create_laundry_order_from_pos(pos_order)

        return result

    def _is_laundry_order(self, pos_order):
        """Check if the POS order contains laundry lines (lines with washing type)"""
        return bool(
            pos_order.lines.filtered(lambda l: l.washing_type_id)
        )

    def _create_laundry_order_from_pos(self, pos_order):
        """Create a laundry order and corresponding washing works from a POS order"""
        LaundryOrder = self.env['laundry.order'].sudo()

        # Avoid duplicate creation
        if LaundryOrder.search([('pos_order_id', '=', pos_order.id)], limit=1):
            return

        order_line_ids = []
        for line in pos_order.lines:
            if not line.washing_type_id:
                continue

            order_line_ids.append((0, 0, {
                'product_id': line.product_id.id,
                'description': line.full_product_name,
                'qty': line.qty,
                'tax_ids': [(6, 0, line.tax_ids.ids)],
                'washing_type_id': line.washing_type_id.id,
                'amount': line.price_subtotal_incl,
                'state': 'draft',
            }))

        if not order_line_ids:
            return

        # ✅ STORE CREATED RECORD
        laundry_order = LaundryOrder.create({
            'order_ref': pos_order.name,
            'pos_order_id': pos_order.id,
            'pos_reference': pos_order.pos_reference,
            'partner_id': pos_order.partner_id.id,
            'partner_invoice_id': pos_order.partner_id.id,
            'partner_shipping_id': pos_order.partner_id.id,
            'laundry_person_id': pos_order.user_id.id,
            'state': 'order',
            'order_line_ids': order_line_ids,
        })

        # --------------------------------------------------
        # CREATE WASHING WORKS ✅
        # --------------------------------------------------
        Washing = self.env['washing.washing'].sudo()

        for line in laundry_order.order_line_ids:
            if not line.washing_type_id:
                continue

            assigned_user = line.washing_type_id.assigned_person_id

            Washing.create({
                'name': f"{line.product_id.display_name} - Washing",
                'user_id': assigned_user.id,
                'description': line.description or line.product_id.display_name,
                'laundry_id': line.id,  # ensure this field exists
                'state': 'draft',
                'washing_date': fields.Datetime.now(),
            })

    def _prepare_invoice_lines(self, move_type):
        """Prepare invoice lines from the POS order lines, including washing type as a note"""
        invoice_lines = []

        for order in self:
            line_values_list = order.with_context(
                invoicing=True
            )._prepare_tax_base_line_values()

            for line_values in line_values_list:
                line = line_values.get('record')

                # ✅ REQUIRED FILTER (same as addons expectation

                invoice_lines_values = order._get_invoice_lines_values(
                    line_values, line, move_type
                )
                invoice_lines.append((0, 0, invoice_lines_values))

                # ✅ YOUR CUSTOM ADDITION
                if line.washing_type_id:
                    invoice_lines.append((0, 0, {
                        'name': line.washing_type_id.name,
                        'display_type': 'line_note',
                    }))

                # ✅ KEEP ADDONS LOGIC (if you had it)
                if line.customer_note:
                    invoice_lines.append((0, 0, {
                        'name': line.customer_note,
                        'display_type': 'line_note',
                    }))

            # Order-level note (same as addons)
            if order.general_customer_note:
                invoice_lines.append((0, 0, {
                    'name': order.general_customer_note,
                    'display_type': 'line_note',
                }))

        return invoice_lines
