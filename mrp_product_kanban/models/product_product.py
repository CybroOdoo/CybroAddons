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
from odoo import fields, models


class ProductProduct(models.Model):
    """ Inherits the model 'product.product' to add extra fields and
    functionalities """
    _inherit = 'product.product'

    mrp_count = fields.Integer(string="Manufacturing",
                               compute="_compute_mrp_count",
                               help="Count of manufacturing orders")
    work_count = fields.Integer(string="Work Order",
                                compute="_compute_work_count",
                                help="Count of work orders")
    bom_count = fields.Integer(string="BOM", compute="_compute_bom_count",
                               help="Count of BOM")

    def action_mrp_orders(self):
        """ Returns the Manufacturing Orders """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manufacturing Orders',
            'view_mode': 'list,form',
            'res_model': 'mrp.production',
            'domain': [('product_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_work_orders(self):
        """ Returns work Orders """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Work Orders',
            'view_mode': 'list,form',
            'res_model': 'mrp.workorder',
            'domain': [('product_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_un_build_orders(self):
        """ Returns un-build Orders """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Unbuild Orders',
            'view_mode': 'list,form',
            'res_model': 'mrp.unbuild',
            'domain': [('product_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_scrap_orders(self):
        """ Returns Scrap Orders """
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('stock.stock_scrapped_moves_action')
        action['name'] = 'Scrap Orders'
        action['domain'] = [('product_id', '=', self.id), ('is_scrap', '=', True)]
        action['context'] = {
            'default_product_id': self.id,
            'default_is_scrap': True,
            'create': False,
        }
        return action

    def action_bom(self):
        """ Returns Boms """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bill of Materials',
            'view_mode': 'list,form',
            'res_model': 'mrp.bom',
            'domain': [('product_tmpl_id', '=', self.product_tmpl_id.id)],
            'context': {'create': False},
        }

    def _compute_mrp_count(self):
        """ Compute the total manufacturing orders of product """
        mrp_data = self.env['mrp.production']._read_group(
            [('product_id', 'in', self.ids)],
            ['product_id'],
            ['__count'],
        )
        mrp_count_map = {product.id: count for product, count in mrp_data}
        for product in self:
            product.mrp_count = mrp_count_map.get(product.id, 0)

    def _compute_work_count(self):
        """ Compute the total work orders of product """
        work_data = self.env['mrp.workorder']._read_group(
            [('product_id', 'in', self.ids)],
            ['product_id'],
            ['__count'],
        )
        work_count_map = {product.id: count for product, count in work_data}
        for product in self:
            product.work_count = work_count_map.get(product.id, 0)

    def _compute_bom_count(self):
        """ Compute the total bom of product """
        tmpl_ids = self.product_tmpl_id.ids
        bom_data = self.env['mrp.bom']._read_group(
            [('product_tmpl_id', 'in', tmpl_ids)],
            ['product_tmpl_id'],
            ['__count'],
        )
        bom_count_map = {tmpl.id: count for tmpl, count in bom_data}
        for product in self:
            product.bom_count = bom_count_map.get(product.product_tmpl_id.id, 0)
