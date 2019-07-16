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


class AccountInvoiceAppend(models.Model):
    _inherit = "account.invoice"

    @api.model
    def create(self, vals):
        if "invoice_line_ids" in vals.keys():
            product_list = []
            new_list = []
            check_list = []
            for obj in vals['invoice_line_ids']:
                if obj[2]:
                    if "product_id" in obj[2]:
                        if obj[2]['product_id'] not in product_list:
                            product_list.append(obj[2]['product_id'])
            for obj in product_list:
                quantity = 0
                for obj1 in vals['invoice_line_ids']:
                    if obj1[2]['product_id'] == obj:
                        quantity += obj1[2]['quantity']
                for obj1 in vals['invoice_line_ids']:
                    if obj1[2]['product_id'] == obj:
                        obj1[2]['quantity'] = quantity
                for obj2 in vals['invoice_line_ids']:
                    if obj2[2]['product_id'] not in check_list:
                        new_list.append(obj2)
                        check_list.append(obj2[2]['product_id'])
            vals['invoice_line_ids'] = new_list
        res = super(AccountInvoiceAppend, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        product_list_ext = []
        product_list_new = []
        if "invoice_line_ids" in vals.keys():
            new_list = vals['invoice_line_ids']
            for att in new_list:
                if att[0] == 4:
                    s = self.invoice_line_ids.browse(att[1])
                    if s.product_id.id not in product_list_ext:
                        product_list_ext.append(s.product_id.id)
                if att[0] == 0:
                    if att[2]['product_id'] not in product_list_new:
                        product_list_new.append(att[2]['product_id'])
                if att[0] == 1:
                    s = self.invoice_line_ids.browse(att[1])
                    if s.product_id.id not in product_list_ext:
                        product_list_ext.append(s.product_id.id)
            pro_list = []

            for obj in product_list_new:
                pro_qty = 0
                if obj in product_list_ext:
                    for att in new_list:
                        if att[0] == 4:
                            o = self.invoice_line_ids.browse(att[1])
                            if o.product_id.id == obj:
                                pro_qty += o.quantity
                        if att[1] == 0:
                            if att[2]['product_id'] == obj:
                                pro_qty += att[2]['quantity']
                        if att[0] == 1:
                            o = self.invoice_line_ids.browse(att[1])
                            if o.product_id.id == obj:
                                pro_qty += att[2]['quantity']
                    for att1 in new_list:
                        if att1[0] == 4:
                            o = self.invoice_line_ids.browse(att1[1])
                            if o.product_id.id == obj:
                                o.quantity = pro_qty
                        if att1[0] == 1:
                            o = self.invoice_line_ids.browse(att1[1])
                            if o.product_id.id == obj:
                                att1[2]['quantity'] = pro_qty

            for obj1 in product_list_new:
                pro_qty = 0
                count = 0
                if obj1 not in product_list_ext:
                    for att1 in new_list:
                        if att1[0] == 0:
                            if att1[2]['product_id'] == obj1:
                                pro_qty += att1[2]['quantity']
                    for att2 in new_list:
                        if att2[0] == 0:

                            if att2[2]['product_id'] == obj1:
                                count += 1
                                if count == 1:
                                    att2[2]['quantity'] = pro_qty
                                    pro_list.append(att2)
            for obj2 in product_list_ext:
                if obj2 not in product_list_new:
                    for att2 in new_list:
                        if att2[0] == 4:
                            o = self.invoice_line_ids.browse(att2[1])
                            if o.product_id.id == obj2:
                                pro_list.append(att2)
            for att3 in new_list:
                if att3[0] == 2:
                    pro_list.append(att3)
                if att3[0] == 1:
                    o = self.invoice_line_ids.browse(att3[1])
                    if "quantity" in att3[2]:
                        o.quantity = att3[2]['quantity']
            vals['invoice_line_ids'] = pro_list
        res = super(AccountInvoiceAppend, self).write(vals)
        return res





















