# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
#
################################################################################
from odoo import models


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """ Create manufacturing order of components in selected BOM """
        for rec in self.order_line:
            if rec.bom_id:
                move_raw = []
                bom_line = self.env['mrp.bom.line'].search(
                    [('bom_id', '=', rec.bom_id.id)])
                for val in bom_line.mapped('product_id'):
                    product_uom_qty = bom_line.filtered(
                        lambda x: x.product_id.id == val.id).product_qty
                    move_raw.append(
                        (0, 0, {
                            'company_id': self.env.user.company_id.id,
                            'product_id': val.id,
                            'product_uom_qty': product_uom_qty *
                                               rec.product_uom_qty,
                            'name': val.name,
                        }))
                self.env['mrp.production'].sudo().create({
                    'product_id': rec.product_id.id,
                    'product_uom_qty': rec.product_uom_qty,
                    'bom_id': rec.bom_id.id,
                    'user_id': self.env.uid,
                    'product_uom_id': rec.product_id.uom_id.id,
                    'company_id': self.env.user.company_id.id,
                    'state': 'confirmed',
                    'product_qty': rec.product_uom_qty,
                    'source': self.name,
                    'move_raw_ids': move_raw
                })
        return super(SaleOrderInherit, self).action_confirm()
