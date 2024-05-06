# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    """
        Extended model for account move lines with catch weight fields.
    """
    _inherit = 'account.move.line'

    cw_qty = fields.Float(string='CW-Qty', default=1.00,
                          help="Catch weight quantity",
                          compute='_compute_cw_qty', digits=(16, 4),
                          readonly=False)
    category_id = fields.Many2one(
        'uom.category', string='Category',
        default=lambda self: self.env.ref('uom.product_uom_categ_kgm'),
        help="Category of the uom")
    cw_uom_id = fields.Many2one('uom.uom', string='Catch Weight UOM',
                                domain="[('category_id', '=', category_id)]",
                                help="Catch weight unit of measure")
    cw_hide = fields.Boolean(string='CW-Hide', default=False,
                             compute='_compute_hide',
                             help="Boolean field to hide the"
                                  " field 'category_id'")

    @api.depends('product_id')
    def _compute_hide(self):
        """To set the visibility of fields"""
        for rec in self:
            rec.cw_uom_id = rec.product_id.cw_uom_id.id
            rec.cw_hide = bool(rec.product_id.catch_weigth_ok)

    @api.onchange('product_id', 'quantity')
    def _onchange_product_id_qty(self):
        """Calculating cw qty and cw uom"""
        for rec in self:
            if rec.product_id.catch_weigth_ok:
                rec.cw_uom_id = rec.product_id.cw_uom_id.id
                if rec.cw_uom_id == rec.product_uom_id:
                    rec.quantity = rec.cw_qty
                else:
                    rec.cw_qty = rec.product_id.average_cw_qty * rec.quantity

    @api.onchange('cw_qty')
    def _onchange_cw_qty(self):
        """Calculate the product qty based on the cw_qty"""
        for rec in self:
            if rec.product_id.catch_weigth_ok and \
                    rec.product_id.average_cw_qty != 0:
                rec.quantity = rec.cw_qty / rec.product_id.average_cw_qty

    def _compute_cw_qty(self):
        """Computing the cw_qty"""
        for rec in self:
            rec.update({
                'cw_qty': rec.product_id.average_cw_qty * rec.quantity})

    @api.onchange('product_uom_id', 'cw_uom_id')
    def compute_weight(self):
        """Calculate the cw weight"""
        for rec in self:
            if (rec.product_id.catch_weigth_ok and rec.cw_uom_id and
                    rec.product_uom_id.category_id == rec.cw_uom_id.category_id):
                rec.cw_qty = rec.cw_uom_id.factor / rec.product_uom_id.factor
