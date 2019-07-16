# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Niyas Raphy(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import api, models


class SaleOrderAppend(models.Model):
    _inherit = "sale.order"

    @api.model
    def create(self, vals):
        if "order_line" in vals.keys():
            product_list = []
            for obj in vals['order_line']:
                if obj[2]['product_id'] not in product_list:
                    product_list.append(obj[2]['product_id'])
            list_new = vals['order_line']
            new_list = []
            for obj in product_list:
                count = 0
                qty = 0
                for element in list_new:
                    if obj == element[2]['product_id']:
                        qty += element[2]['product_uom_qty']
                for ele in list_new:
                    if obj == ele[2]['product_id']:
                        count += 1
                        if count == 1:
                            ele[2]['product_uom_qty'] = qty
                            ele[2]['product_uos_qty'] = qty
                            new_list.append(ele)
            vals['order_line'] = new_list
        res = super(SaleOrderAppend, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        product_list_ext = []
        product_list_new = []
        if "order_line" in vals.keys():
            new_list = vals['order_line']
            pro_list = []
            for att in new_list:
                if att[0] == 4:
                    s = self.order_line.browse(att[1])
                    if s.product_id not in product_list_ext:
                        product_list_ext.append(s.product_id.id)
                if att[0] == 1:
                    s = self.order_line.browse(att[1])
                    if s.product_id not in product_list_ext:
                        product_list_ext.append(s.product_id.id)
                if att[0] == 0:
                    if att[2]['product_id'] not in product_list_new:
                        product_list_new.append(att[2]['product_id'])
            for obj in product_list_new:
                pro_qty = 0
                if obj in product_list_ext:
                    for att in new_list:
                        if att[0] == 4:
                            o = self.order_line.browse(att[1])
                            if o.product_id.id == obj:
                                pro_qty += o.product_uom_qty
                        if att[0] == 1:
                            o = self.order_line.browse(att[1])
                            if o.product_id.id == obj:
                                pro_qty += att[2]['product_uom_qty']
                        if att[1] == 0:
                            if att[2]['product_id'] == obj:
                                pro_qty += att[2]['product_uom_qty']

                    for att1 in new_list:
                        if att1[0] == 4:
                            o = self.order_line.browse(att1[1])
                            if o.product_id.id == obj:
                                    o.product_uom_qty = pro_qty
                                    o.product_uos_qty = pro_qty
                        if att1[0] == 1:
                            o = self.order_line.browse(att1[1])
                            if o.product_id.id == obj:
                                att1[2]['product_uom_qty'] = pro_qty
                                o.product_uom_qty = pro_qty
            for obj1 in product_list_new:
                pro_qty = 0
                count = 0
                if obj1 not in product_list_ext:
                    for att1 in new_list:
                        if att1[0] == 0:
                            if att1[2]['product_id'] == obj1:
                                pro_qty += att1[2]['product_uom_qty']
                    for att2 in new_list:
                        if att2[0] == 0:
                            if att2[2]['product_id'] == obj1:
                                count += 1
                                if count == 1:
                                    att2[2]['product_uom_qty'] = pro_qty
                                    att2[2]['product_uos_qty'] = pro_qty
                                    pro_list.append(att2)

            for obj2 in product_list_ext:
                if obj2 not in product_list_new:
                    for att2 in new_list:
                        if att2[0] == 4:
                            o = self.order_line.browse(att2[1])
                            if o.product_id.id == obj2:
                                pro_list.append(att2)
            for att3 in new_list:
                if att3[0] == 2:
                    pro_list.append(att3)
                if att3[0] == 1:
                    o = self.order_line.browse(att3[1])
                    o.product_uom_qty = att3[2]['product_uom_qty']

            vals['order_line'] = pro_list
        res = super(SaleOrderAppend, self).write(vals)
        return res

























