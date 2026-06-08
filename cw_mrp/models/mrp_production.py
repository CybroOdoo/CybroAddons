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


class MrpProduction(models.Model):
    """Inherited model 'mrp.production'"""
    _inherit = 'mrp.production'

    cw_qty = fields.Float(string='CW-Qty', digits=(16, 4),
                          help="Catch weight quantity")
    cw_uom_id = fields.Many2one('uom.uom', string='CW-Uom',
                                help="Catch weight unit of measure.",
                                store=True)
    toggle_cw = fields.Boolean(string='is_cw_product', default=False,
                               help="Check whether uom product or not.")

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        """Updating the cw qty and cw uom on changing the product"""
        self.toggle_cw = bool(self.product_tmpl_id.catch_weigth_ok)
        self.cw_uom_id = self.product_tmpl_id.cw_uom_id
        self.cw_qty = self.product_tmpl_id.average_cw_qty

    @api.onchange('cw_qty')
    def _onchange_cw_qty(self):
        """Updating the product qty on changing the cw quantity"""
        if self.toggle_cw and self.product_tmpl_id.average_cw_qty != 0:
            self.product_qty = self.cw_qty / self.product_tmpl_id.average_cw_qty

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        """Updating cw qty on changing the product quantity"""
        if self.toggle_cw:
            self.cw_qty = self.product_tmpl_id.average_cw_qty * self.product_qty
