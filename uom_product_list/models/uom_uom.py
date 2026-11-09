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
from odoo import fields, models, _


class Uom(models.Model):
    """Class inheriting uom model for listing out the products in their
    corresponding unit of measure."""
    _inherit = 'uom.uom'

    products_uom = fields.Integer(compute='_compute_products_uom',
                                  string="Products",
                                  help="Compute product count in UOM")

    def action_view_products(self):
        """Smart tab for viewing products with corresponding UOM"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Products'),
            'view_mode': 'kanban,form',
            'res_model': 'product.template',
            'domain': [('uom_id', '=', self.id)],
            'context': "{'create': False}",
        }

    def _compute_products_uom(self):
        """Function for computing the count of products with the
        corresponding UOM"""
        for record in self:
            record.products_uom = self.env['product.template'].search_count(
                [('uom_id', '=', record.id)])
