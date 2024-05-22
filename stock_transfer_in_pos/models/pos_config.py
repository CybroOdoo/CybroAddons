# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R(odoo@cybrosys.com)
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

###############################################################################
from odoo import api, fields, models
from odoo.fields import Command


class PosConfig(models.Model):
    """Inherited model for adding new field to configuration settings
                that allows to transfer stock from pos session"""
    _inherit = 'pos.config'

    stock_transfer = fields.Boolean(string="Enable Stock Transfer",
                                    help="Enable if you want to transfer "
                                         "stock from PoS session")

    @api.model
    def get_stock_transfer_list(self):
        """To get selection field values of stock transfer popup

            :return dict: returns list of dictionary with stock picking types,
            stock location, and stock warehouse.
        """
        main = {}
        main['picking_type'] = self.env['stock.picking.type'].search_read(
            [('company_id', '=', self.env.user.company_id.id)],
            ['display_name', 'code'])
        main['location'] = self.env['stock.location'].search_read([], [
            'display_name'])
        main['wh_stock'] = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.user.company_id.id)]).lot_stock_id.id
        return main

    @api.model
    def create_transfer(self, pick_id, source_id, dest_id, state, line):
        """ Create a stock transfer based on the popup value

            :param pick_id(string): id of stock picking type
            :param source_id(string): id of source stock location
            :param dest_id(string): id of destination stock location
            :param state(string): state of stock picking
            :param line(dictionary): dictionary values with product ids and  quantity

            :return dict: returns dictionary of values with created stock transfer
                id and name
        """
        transfer = self.env['stock.picking'].create({
            'picking_type_id': int(pick_id),
            'location_id': int(source_id),
            'location_dest_id': int(dest_id),
            'move_ids': [Command.create({
                'product_id': line['pro_id'][rec],
                'product_uom_qty': line['qty'][rec],
                'location_id': int(source_id),
                'location_dest_id': int(dest_id),
                'name': "Product"
            }) for rec in range(len(line['pro_id']))],
        })
        transfer.write({'state': state})
        return {
            'id': transfer.id,
            'name': transfer.name
        }
