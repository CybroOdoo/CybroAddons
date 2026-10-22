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
from odoo import Command, api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    """ Inherits sale.order.line to add the functions for checking the
    visibility of the pricelists in order lines and applying the pricelists
    to order lines. """
    _inherit = 'sale.order.line'

    pricelist_visibility = fields.Boolean(
        compute="_compute_pricelist_visibility", string="Pricelist Visible",
        help="Multi Pricelist enabled or not")
    applied_pricelist_id = fields.Many2one(
        'product.pricelist',
        string="Pricelist",
        help="Pricelist that is applied to the order line.")

    def _get_pricelist_rule(self, pricelist):
        """ Return the rule (product.pricelist.item record, possibly empty) of
        the given pricelist that applies to this line's product, quantity and
        unit of measure. """
        self.ensure_one()
        rule = pricelist._get_product_rule(
            self.product_id,
            quantity=self.product_uom_qty or 1.0,
            uom=self.product_uom_id,
            date=self.order_id.date_order,
        )
        if isinstance(rule, models.BaseModel):
            return rule
        return self.env['product.pricelist.item'].browse(rule)

    def _get_pricelist_price(self):
        """ Overriding the _get_pricelist_price method to apply multiple
        pricelists """
        self.ensure_one()
        self.product_id.ensure_one()
        if self.applied_pricelist_id:
            self.pricelist_item_id = self._get_pricelist_rule(
                self.applied_pricelist_id)
        return self.unit_price(self.pricelist_item_id)

    def apply_pricelist(self):
        """ Open a wizard listing every pricelist that has a rule for the
        product of this line, with the unit price each one would give. """
        self.ensure_one()
        if not self.product_id:
            raise UserError(self.env._(
                "Please select a product before applying a pricelist."))
        pricelists = self.env['product.pricelist'].search([
            ('active', '=', True),
            ('company_id', 'in', [False, self.company_id.id]),
        ])
        wizard_lines = []
        for pricelist in pricelists:
            rule = self._get_pricelist_rule(pricelist)
            if not rule:
                continue
            wizard_lines.append(Command.create({
                'pricelist_id': pricelist.id,
                'product_id': self.product_id.id,
                'unit_price': self.unit_price(rule),
                'unit_cost': self.product_id.standard_price,
                'uom_id': self.product_uom_id.id,
            }))
        if not wizard_lines:
            raise UserError(self.env._(
                "No price list is configured for this product!"))
        pricelist_wizard = self.env['pricelist.product'].create({
            'order_line_id': self.id,
            'line_ids': wizard_lines,
        })
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'name': self.env._("Select Pricelist"),
            'view_mode': 'form',
            'view_id': self.env.ref(
                "multi_pricelist.pricelist_wizard_view_form").id,
            'res_model': 'pricelist.product',
            'res_id': pricelist_wizard.id,
        }

    @api.depends('order_id.state')
    def _compute_pricelist_visibility(self):
        """ Computes pricelist_visibility by checking the config parameter """
        param = self.env['ir.config_parameter'].sudo().get_str(
            'multi_pricelist.multi_pricelist')
        enabled = param in ('True', 'true', '1')
        for rec in self:
            rec.pricelist_visibility = enabled and rec.order_id.state not in (
                'sale', 'done', 'cancel')

    def unit_price(self, price):
        """ Compute the unit price of the product of this line according to
        the given pricelist item, using the standard pricelist engine so that
        every rule type behaves exactly as it does in core. """
        self.ensure_one()
        return price._compute_price(
            product=self.product_id.with_context(
                **self._get_product_price_context()),
            quantity=self.product_uom_qty or 1.0,
            uom=self.product_uom_id,
            date=self.order_id.date_order,
            currency=self.currency_id,
        )
