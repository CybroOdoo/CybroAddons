# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: SAYOOJ A O (<https://www.cybrosys.com>)
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
###################################################################################

from odoo import models


class PickingInvoiceWizard(models.TransientModel):
    _name = 'picking.invoice.wizard'
    _description = "Create Invoice from picking"

    def picking_multi_invoice(self):
        active_ids = self._context.get('active_ids')
        picking_ids = self.env['stock.picking'].browse(active_ids)
        picking_id = picking_ids.filtered(lambda x: x.state == 'done' and x.invoice_count == 0)
        for picking in picking_id:
            if picking.picking_type_id.code == 'incoming' and not picking.is_return:
                picking.create_bill()
            if picking.picking_type_id.code == 'outgoing' and not picking.is_return:
                picking.create_invoice()
            if picking.picking_type_id.code == 'incoming' and picking.is_return:
                picking.create_vendor_credit()
            if picking.picking_type_id.code == 'outgoing' and picking.is_return:
                picking.create_customer_credit()
