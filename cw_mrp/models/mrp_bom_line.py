# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ahammed Harshad P (odoo@cybrosys.info)
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
#############################################################################
from odoo import api, fields, models


class MrpBomLine(models.Model):
    """Inherited model 'mrp.bom.line'"""
    _inherit = 'mrp.bom.line'

    cw_qty = fields.Float(string='CW-Qty', digits=(16, 4),
                          help="Catch weight quantity")
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                store=True, help="Catch Weight Uom")
    cw_hide = fields.Boolean(string='CW-Hide', default=False,
                             help="Check whether uom product or not.")

    @api.onchange('product_id', 'product_qty')
    def _onchange_product_id_product_qty(self):
        """Update cw qty and uom based on product and quantity changes"""
        for rec in self:
            rec.cw_uom_id = rec.product_id.cw_uom_id.id
            rec.cw_hide = bool(rec.product_id.catch_weigth_ok)
            if rec.cw_uom_id == rec.product_uom_id:
                rec.cw_qty = rec.product_qty
            else:
                rec.cw_qty = rec.product_qty * rec.product_id.average_cw_qty

    @api.onchange('cw_qty')
    def _onchange_cw_qty(self):
        """Update product qty based on cw quantity"""
        for rec in self:
            if rec.product_id.catch_weigth_ok and rec.product_qty and rec.cw_qty != 0 and rec.product_id.average_cw_qty != 0:
                if rec.cw_uom_id == rec.product_uom_id:
                    rec.product_qty = rec.cw_qty
                else:
                    rec.product_qty = rec.cw_qty / rec.product_id.average_cw_qty

    @api.onchange('product_uom_id', 'cw_uom_id')
    def _onchange_product_uom_id_cw_uom_id(self):
        """Update cw qty based on product uom"""
        for rec in self:
            if rec.product_id.catch_weigth_ok and rec.cw_uom_id and rec.product_uom_id == rec.cw_uom_id:
                rec.cw_qty = rec.cw_uom_id.factor / rec.product_uom_id.factor
