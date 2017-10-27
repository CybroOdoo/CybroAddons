# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Avinash Nk(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
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
from odoo import models, api, _
from odoo.exceptions import UserError


class ExpiryDateWarning(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        super(ExpiryDateWarning, self).product_uom_change()
        if self.product_id:
            total_quantity = 0.0
            product_sale = self.product_id
            quantity_in_lot = self.env['stock.quant'].search([])
            lot_number_obj = self.env['stock.production.lot']
            lot_number_obj_specific = lot_number_obj.search([])
            for records in lot_number_obj_specific:
                dates = date.today()
                if records.life_date:
                    dates = datetime.strptime(records.life_date, '%Y-%m-%d %H:%M:%S').date()
                if records.product_id.id == product_sale.id and dates < date.today():
                    for values in quantity_in_lot:
                        if values.lot_id.id == records.id and values.product_id.id == product_sale.id:
                            total_quantity = total_quantity+values.qty
            good_products = self.product_id.qty_available - total_quantity
            if good_products < self.product_uom_qty:
                warning_mess = {
                    'title': _('Not enough good products!'),
                    'message': _(
                        'You plan to sell %.2f %s but you only have %.2f %s Good Products available!\n'
                        'The stock on hand is %.2f %s.') % (
                               self.product_uom_qty, self.product_uom.name, good_products, self.product_id.uom_id.name,
                               self.product_id.qty_available, self.product_id.uom_id.name)
                }
                return {'warning': warning_mess}


class ExpiryDateStockPackOperation(models.Model):
    _inherit = "stock.pack.operation"

    @api.multi
    def save(self):
        res = super(ExpiryDateStockPackOperation, self).save()
        lots = [x.lot_id for x in self.pack_lot_ids]
        lot_list = []
        for lot in lots:
            if self.product_id == lot.product_id:
                if lot.life_date:
                    today = date.today()
                    life_date = datetime.strptime(lot.life_date, '%Y-%m-%d %H:%M:%S').date()
                    if life_date < today:
                        lot_list.append(str(lot.name))
        if len(lot_list) == 1:
            raise UserError(_('Product in this lot number is expired : %s' % lot_list[0]))
        elif len(lot_list) > 1:
            raise UserError(_('Products in these lot numbers are expired : %s' % lot_list))
        return res
