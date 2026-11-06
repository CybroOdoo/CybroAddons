# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    cw_qty = fields.Float(string='CW-Qty', digits=(16, 4),
                          help="The catch weight quantity of the product.")
    cw_uom_id = fields.Many2one(
        'uom.uom', string='CW-Uom',
        compute='_compute_cw_uom_id', store=True, readonly=False,
        help="The catch weight unit of measure used for this product.")
    cw_delivered = fields.Float(
        string='CW-Delivered', readonly=True,
        compute='_compute_cw_delivered_invoiced', digits=(16, 4),
        help="The delivered quantity in catch weight units.")
    cw_invoiced = fields.Float(
        string='CW-Invoiced', readonly=True,
        digits=(16, 4),
        compute='_compute_cw_delivered_invoiced',
        help="The invoiced quantity in catch weight units.")
    is_cw_product = fields.Boolean(
        string='Is CW Product',
        compute="_compute_is_cw_product", default=False,
        help="A flag indicating whether this is a catch weight product.")

    @api.depends('product_id')
    def _compute_is_cw_product(self):
        """Flag the line when its product is a catch weight product"""
        for rec in self:
            rec.is_cw_product = bool(rec.product_id.catch_weigth_ok)

    @api.depends('product_id')
    def _compute_cw_uom_id(self):
        """Compute the catch weight unit of measure from the product."""
        for rec in self:
            rec.cw_uom_id = rec.product_id.cw_uom_id

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_id_product_uom_qty(self):
        """Calculate the CW unit of measure, CW quantity and price when the
        product or its quantity changes"""
        for rec in self:
            if rec.product_id.catch_weigth_ok:
                rec.price_unit = rec.product_id.list_price
                rec.cw_uom_id = rec.product_id.cw_uom_id.id
                if rec.cw_uom_id == rec.product_uom_id:
                    rec.cw_qty = rec.product_uom_qty
                else:
                    rec.cw_qty = (rec.product_uom_qty *
                                  rec.product_id.average_cw_qty)

    @api.onchange('cw_qty')
    def _onchange_cw_qty(self):
        """Calculate the product quantity from the CW quantity"""
        for rec in self:
            if (rec.product_id.catch_weigth_ok
                    and rec.product_id.average_cw_qty != 0):
                if rec.cw_uom_id == rec.product_uom_id:
                    rec.product_uom_qty = rec.cw_qty
                else:
                    rec.product_uom_qty = (rec.cw_qty /
                                           rec.product_id.average_cw_qty)

    @api.depends('qty_delivered', 'qty_invoiced', 'product_id.average_cw_qty')
    def _compute_cw_delivered_invoiced(self):
        """Calculate the CW delivered and CW invoiced quantities"""
        for rec in self:
            rec.update({
                'cw_delivered': (rec.qty_delivered *
                                 rec.product_id.average_cw_qty),
                'cw_invoiced': rec.qty_invoiced * rec.product_id.average_cw_qty
            })