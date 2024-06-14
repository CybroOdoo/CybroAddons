# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
###############################################################################
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
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manufacturing Orders',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'domain': [('product_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def action_work_orders(self):
        """ Returns the work Orders """
        return {
            'type': 'ir.actions.act_window',
            'name': 'WorkOrders',
            'view_mode': 'tree,form',
            'res_model': 'mrp.workorder',
            'domain': [('product_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def action_un_build_orders(self):
        """ Returns the un-build Orders """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Unbuild Orders',
            'view_mode': 'tree,form',
            'res_model': 'mrp.unbuild',
            'domain': [('product_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def action_scrap_orders(self):
        """ Returns the Scrap Orders """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Scrap Orders',
            'view_mode': 'tree,form',
            'res_model': 'stock.scrap',
            'domain': [('product_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def action_bom(self):
        """ Returns the Boms """
        return {
            'type': 'ir.actions.act_window',
            'name': 'BOM',
            'view_mode': 'tree,form',
            'res_model': 'mrp.bom',
            'domain': [('product_tmpl_id', '=', self.product_tmpl_id.id)],
            'context': "{'create': False}"
        }

    def _compute_mrp_count(self):
        """ Compute the total manufacturing orders of product """
        for product in self:
            product.mrp_count = self.env['mrp.production'].search_count(
                [('product_id', '=', product.id)])

    def _compute_work_count(self):
        """ Compute the total working orders of product """
        for product in self:
            product.work_count = self.env['mrp.workorder'].search_count(
                [('product_id', '=', product.id)])

    def _compute_bom_count(self):
        """ Compute the total bom of product """
        for product in self:
            product.bom_count = self.env['mrp.bom'].search_count(
                [('product_tmpl_id', '=', product.product_tmpl_id.id)])
