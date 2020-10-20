# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Avinash Nk(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ExpiryDateWarning(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id', 'product_uom_qty')
    def product_uom_change(self):
        print("uom")
        if self.product_id:
            total_quantity = 0.0
            product_sale = self.product_id
            quantity_in_lot = self.env['stock.quant'].search([])
            lot_number_obj = self.env['stock.production.lot']
            lot_number_obj_specific = lot_number_obj.search([])
            for records in lot_number_obj_specific:
                dates = date.today()
                print(dates,"dates")
                print(dates, "dates")
                if records.expiration_date:
                    dates = datetime.strptime(str(records.expiration_date), '%Y-%m-%d %H:%M:%S')
                    print(dates, "datessssssssssss")
                if records.product_id.id == product_sale.id:
                    if records.expiration_date and records.expiration_date.date() < date.today():
                        for values in quantity_in_lot:
                            if values.lot_id.id == records.id and values.product_id.id == product_sale.id:
                                if values.quantity >= 0:
                                    total_quantity = total_quantity + values.quantity
                    # elif records.product_id.id == product_sale.id and dates.date() is False:
                #     raise ValidationError(_("Set lot number and expiration date."))
            good_products = self.product_id.qty_available - total_quantity
            if good_products < self.product_uom_qty:
                warning_mess = {
                    'title': _('Not enough good products!'),
                    'message': _(
                        'You plan to sell %.2f %s but you only have %.2f %s good products available!\n'
                        'The stock on hand is %.2f %s.') % (
                                   self.product_uom_qty, self.product_uom.name, good_products,
                                   self.product_id.uom_id.name,
                                   self.product_id.qty_available, self.product_id.uom_id.name)
                }
                return {'warning': warning_mess}


class ExpiryDateStockPackOperation(models.Model):
    _inherit = 'stock.picking'

    @api.onchange('move_line_ids_without_package')
    def move_line_ids_change(self):
        print("move_line_ids_change")
        lots = self.move_line_ids.lot_id
        lot_list = []
        for lot in lots:
            if self.product_id == lot.product_id:
                if lot.expiration_date:
                    today = date.today()
                    expiration_date = datetime.strptime(str(lot.expiration_date), '%Y-%m-%d %H:%M:%S')
                    if expiration_date.date() < today:
                        lot_list.append(str(lot.name))
        if len(lot_list) == 1:
            raise UserError(_('Product in this lot number is expired : %s' % lot_list[0]))
        elif len(lot_list) > 1:
            raise UserError(_('Products in these lot numbers are expired : %s' % lot_list))
