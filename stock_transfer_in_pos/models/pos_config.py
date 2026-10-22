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
from odoo.exceptions import AccessError, UserError
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
        company_id = self.env.company.id
        main['picking_type'] = self.env['stock.picking.type'].search_read(
            [('company_id', '=', company_id)],
            ['display_name', 'code', 'default_location_src_id', 'default_location_dest_id'])
        main['location'] = self.env['stock.location'].search_read(
            [
                ('usage', 'in', ['internal', 'transit']),
                '|', ('company_id', '=', False), ('company_id', '=', company_id),
            ],
            ['display_name'])
        wh = self.env['stock.warehouse'].search(
            [('company_id', '=', company_id)], limit=1)
        main['wh_stock'] = wh.lot_stock_id.id if wh else False
        return main

    @api.model
    def create_transfer(self, config_id, pick_id, source_id, dest_id, state, line):
        """ Create a stock transfer based on the popup value

            :param config_id(int): id of the POS config
            :param pick_id(string): id of stock picking type
            :param source_id(string): id of source stock location
            :param dest_id(string): id of destination stock location
            :param state(string): state of stock picking
            :param line(dictionary): dictionary values with product ids and quantity

            :return dict: returns dictionary of values with created stock transfer
                id and name
        """
        pos_config = self.browse(int(config_id))
        pos_config.check_access('read')
        if not pos_config.stock_transfer:
            raise UserError(self.env._("Stock transfer is not enabled for this Point of Sale."))

        if not self.env.user.has_group('stock.group_stock_user'):
            raise AccessError(self.env._("You do not have the required permissions to perform stock transfers. Stock user access is required."))

        picking_type = self.env['stock.picking.type'].browse(int(pick_id))
        wh = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1)

        src_location_id = int(source_id) if source_id else (
            picking_type.default_location_src_id.id or (wh.lot_stock_id.id if wh else False)
        )
        dest_location_id = int(dest_id) if dest_id else (
            picking_type.default_location_dest_id.id or (wh.lot_stock_id.id if wh else False)
        )

        moves = []
        for rec in range(len(line['pro_id'])):
            product = self.env['product.product'].browse(line['pro_id'][rec])
            moves.append(Command.create({
                'product_id': product.id,
                'product_uom_qty': line['qty'][rec],
                'uom_id': product.uom_id.id,
                'location_id': src_location_id,
                'location_dest_id': dest_location_id,
            }))

        transfer = self.env['stock.picking'].create({
            'picking_type_id': int(pick_id),
            'location_id': src_location_id,
            'location_dest_id': dest_location_id,
            'move_ids': moves,
        })

        if state in ['assigned', 'done']:
            transfer.action_confirm()
            transfer.action_assign()
            if state == 'done':
                for move in transfer.move_ids:
                    move.quantity = move.product_uom_qty
                transfer.button_validate()

        return {
            'id': transfer.id,
            'name': transfer.name
        }
