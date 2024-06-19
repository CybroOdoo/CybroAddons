# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu KP @ Cybrosys, (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.

################################################################################
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    consignment_id = fields.Many2one('sale.consignment',
                                     help='Related Consignment Id')

    def button_validate(self):
        res = super().button_validate()
        consignment_id = self.sale_id.consignment_id
        sale_order = self.env['sale.order'].search([
            ('consignment_id', '=', consignment_id.id)])
        for record in consignment_id.consignment_line_ids:
            quantity = sum(
                rec.product_uom_qty for order in sale_order for rec in
                order.order_line if rec.product_id.id == record.product_id.id)
            record.done_quantity = quantity
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        location_dest_id = int(self.env['ir.config_parameter'].get_param(
            'sale_consignment.location_dest_id'))
        sale_name = res.origin
        sale = self.env['sale.order'].search([('name', '=', sale_name)])
        if sale.consignment_id:
            res.location_id = location_dest_id
        return res
