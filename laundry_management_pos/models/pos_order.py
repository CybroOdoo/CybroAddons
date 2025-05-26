# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
from datetime import datetime
from odoo import api, fields, models, _
from odoo.tools import float_compare, float_repr


class PosOrderLine(models.Model):
    """ This class is inherited for model pos_order_line.
            It contains field and the functions for the model

            Methods:
                _export_for_ui(self, orderline):
                    Supering the export_for_ui function for generating
                    the washing type in the order line for the model.

                _order_line_fields(self, line, session_id):
                    Action perform to adding order-line details in the pos orders.
    """
    _inherit = 'pos.order.line'

    washing_type_id = fields.Many2one('washing.type',
                                      String='Washing Type',
                                      help='The many2one filed that related'
                                           ' to the washing type')

    def _export_for_ui(self, orderline):
        """super the exporting function in the pos order line"""
        result = super()._export_for_ui(orderline)
        result['washing_type_id'] = \
            orderline.washing_type.read(fields=['name'])[0]
        return result

    def _order_line_fields(self, line, session_id):
        """
            Adding order-line details in the pos orders
        """
        result = super()._order_line_fields(line, session_id)
        vals = result[2]
        washing_type_id = line[2].get('washingType_id')
        new_values = {'washing_type_id': int(washing_type_id) if washing_type_id else False}
        vals.update(new_values)
        return result


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
    def create_from_ui(self, orders, draft=False):
        """ Create and update Orders from the frontend PoS application.
        """
        order = super(PosOrder, self).create_from_ui(orders=orders,
                                                     draft=draft)
        if order:
            order_id = order[0]['id']
            values = self.env['pos.order'].browse(order_id)
            lines = []
            for rec in values.lines:
                if rec.washing_type_id:
                    values.write({
                        'laundry_order': True,
                    })
                vals = (0, 0, {
                    'product_id': rec.product_id.id,
                    'description': rec.full_product_name,
                    'qty': rec.qty,
                    'state': 'done',
                    'tax_ids': [(6, 0, rec.tax_ids.ids)],
                    'washing_type': rec.washing_type_id.id,
                    'amount': rec.price_subtotal_incl,
                })
                lines.append(vals)
            if values.laundry_order:
                values.action_pos_order_invoice()
                laundry_order = self.env['laundry.order'].sudo().create({
                    'order_ref': values.name,
                    'pos_order_id': values.id,
                    'pos_reference': values.pos_reference,
                    'partner_id': values.partner_id.id,
                    'partner_invoice_id': values.partner_id.id,
                    'partner_shipping_id': values.partner_id.id,
                    'laundry_person': values.user_id.id,
                    'state': 'done',
                    'order_lines': lines,
                })
                for each in laundry_order:
                    for obj in each.order_lines:
                        self.env['washing.washing'].create(
                            {'name': obj.product_id.name + '-Washing',
                             'user_id': obj.washing_type.assigned_person.id,
                             'description': obj.description,
                             'laundry_obj': obj.id,
                             'state': 'done',
                             'washing_date': datetime.now().strftime(
                                 '%Y-%m-%d %H:%M:%S')})
        return order

    def _prepare_invoice_lines(self):
        """
            Invoice for the corresponding POS order
        """
        sign = 1 if self.amount_total >= 0 else -1
        line_values_list = self._prepare_tax_base_line_values(sign=sign)
        invoice_lines = []
        for line_values in line_values_list:
            line = line_values['record']
            invoice_lines_values = self._get_invoice_lines_values(line_values,
                                                                  line)
            invoice_lines.append((0, None, invoice_lines_values))
            if (
                    line.order_id.pricelist_id.discount_policy == 'without_discount' and
                    float_compare(line.price_unit, line.product_id.lst_price,
                                  precision_rounding=self.currency_id.rounding) < 0):
                invoice_lines.append((0, None, {
                    'name': _('Price discount from %s -> %s',
                              float_repr(line.product_id.lst_price,
                                         self.currency_id.decimal_places),
                              float_repr(line.price_unit,
                                         self.currency_id.decimal_places)),
                    'display_type': 'line_note',
                }))
            if line.customer_note:
                invoice_lines.append((0, None, {
                    'name': line.customer_note,
                    'display_type': 'line_note',
                }))
            if line.washing_type_id:
                invoice_lines.append((0, None, {
                    'name': line.washing_type_id.name,
                    'display_type': 'line_note',
                }))
        return invoice_lines
