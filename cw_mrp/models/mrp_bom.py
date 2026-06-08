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


class MrpBom(models.Model):
    """Inherited model 'mrp.bom'"""
    _inherit = 'mrp.bom'

    cw_qty = fields.Float(string='CW-Qty', digits=(16, 4),
                          help="Catch weight quantity")
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                help="Catch weight unit of measure",
                                store=True)
    toggle_cw = fields.Boolean(string='is_cw_product', default=False,
                               help="Check whether uom product or not.")

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        """Calculating cw qty and cw uom on changing the product"""
        self.toggle_cw = bool(self.product_tmpl_id.catch_weigth_ok)
        self.cw_uom_id = self.product_tmpl_id.cw_uom_id
        self.cw_qty = self.product_tmpl_id.average_cw_qty

    @api.onchange('cw_qty')
    def _onchange_cw_qty(self):
        """Calculating product qty on changing the cw quantity"""
        if self.toggle_cw and self.product_tmpl_id.average_cw_qty != 0:
            if self.cw_uom_id == self.product_uom_id:
                self.product_qty = self.cw_qty
            else:
                self.product_qty = self.cw_qty / self.product_tmpl_id.average_cw_qty

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        """Calculating cw qty on changing the product quantity"""
        if self.toggle_cw:
            if self.cw_uom_id == self.product_uom_id:
                self.cw_qty = self.product_qty
            else:
                self.cw_qty = self.product_tmpl_id.average_cw_qty * self.product_qty

    @api.onchange('product_uom_id', 'cw_uom_id')
    def _onchange_product_uom_id_cw_uom_id(self):
        """Calculating the cw qty based on product uom"""
        if (self.product_tmpl_id.catch_weigth_ok and self.cw_uom_id and
                self.product_uom_id == self.cw_uom_id):
            self.cw_qty = self.cw_uom_id.factor / self.product_uom_id.factor
