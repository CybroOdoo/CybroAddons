# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.1
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
from odoo import http
from odoo.http import request


class CustomBarcode(http.Controller):
    """
    In the class CustomBarcode checking the product/location/operation type/ batch
    while scanning a barcode.
    """

    @property
    def barcode_model(self):
        """
        Provides access to the 'barcode.management' model in Odoo.

        Returns:
            Model: The 'barcode.management' model from the Odoo environment.
        """
        return request.env["barcode.management"]

    @http.route('/barcode/barcode-scanned', type='json', auth='user')
    def barcode_scanned_operation(self, barcode, picking_id, batch_id=False):
        """
        Handles the barcode scanning operation for a given stock picking operation.

        Args:
            barcode (str): The barcode that has been scanned.
            picking_id (int): The picking id of the operation.
            batch_id (int) Optional: The ID of the batch transfer.
        Returns:
            dict: The result of searching for the scanned barcode in the models related to the provided operation ID.
        """
        return self.barcode_model.search_barcode_in_models(barcode, picking_id, batch_id)

    @http.route('/barcode/main-barcode', type='json')
    def product_barcode(self, code, company_id):
        """Check if the scanned item is a product, location, or operation type and return corresponding values."""
        barcode_product = request.env['product.product'].search([('barcode', '=', code)])
        barcode_location = request.env['stock.location'].search([('barcode', '=', code)])
        barcode_picking_type = request.env['stock.picking.type'].search([('barcode', '=', code)])
        data = {
            'type': 'no_data',
        }
        if barcode_product:
            data = {
                'id': barcode_product.id,
                'type': 'product',
                'name': barcode_product.name
            }
        elif barcode_location:
            picking_type = request.env['stock.picking.type'].search([('code', '=', 'internal'),
                                                                     ('company_id', '=', company_id)], limit=1)
            stock_transfer = request.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': barcode_location.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'with_barcode': True
            })

            data = {
                'location_id': barcode_location.id,
                'location_name': barcode_location.complete_name,
                'type': 'location',
                'stock_transfer_id': stock_transfer.id,
                'stock_transfer_name': stock_transfer.name
            }
        elif barcode_picking_type:
            stock_transfer = request.env['stock.picking'].create({
                'picking_type_id': barcode_picking_type.id,
                'location_id': barcode_picking_type.default_location_src_id.id if barcode_picking_type.
                default_location_src_id else request.env.ref('stock.stock_location_suppliers').id,
                'location_dest_id': barcode_picking_type.default_location_dest_id.id if barcode_picking_type.
                default_location_dest_id else request.env.ref('stock.stock_location_customers').id,
                'with_barcode': True
            })
            data = {
                'type': 'operation_type',
                'stock_transfer_id': stock_transfer.id,
                'stock_transfer_name': stock_transfer.name
            }
        return data

    @http.route('/inventory_commands', type='json')
    def print_pdf_for_inventory_commands(self, code, id):
        """
        Function For printing delivery slip or operation report or performing
        'action_record_components' action
        """
        obj = request.env['stock.picking'].browse(int(id))
        if code == 'action_slip':
            return request.env.ref('stock.action_report_delivery').report_action(obj)
        elif code == 'action_picking':
            return request.env.ref('stock.action_report_picking').report_action(obj)
        elif code == 'print_batch':
            return request.env.ref('stock_picking_batch.action_report_picking_batch').report_action(
                request.env['stock.picking.batch'].browse(int(id)))
        else:
            pick_id = request.env['stock.picking'].browse(int(id))
            if pick_id.display_action_record_components == 'mandatory':
                pick_id.action_record_components()
            return True

    @http.route('/barcode-location/product-barcode', type='json')
    def product_location_barcode(self, code, location_id, destination, pick_id):
        """Retrieve data for scanned barcode item from the Barcode transfer view and return the corresponding record in stock.move."""
        barcode_location = request.env['stock.location'].search([('barcode', '=', code)])
        barcode_product = request.env['product.product'].search([('barcode', '=', code)])
        barcode_package = request.env['product.packaging'].search([('barcode', '=', code)])
        if barcode_location:
            data = {
                'type': 'location',
                'id': barcode_location.id,
                'name': barcode_location.complete_name
            }
        elif barcode_package:
            stock_move = request.env['stock.move'].search([('picking_id', '=', int(pick_id)),
                                                           ('product_id', '=', barcode_package.product_id.id)])
            if stock_move:
                stock_move.done_quantity += int(barcode_package.qty)
                data = {
                    'type': 'exist_product',
                    'id': stock_move.id,
                    'quantity': stock_move.done_quantity,
                    'move_lines': stock_move.move_line_ids.read()
                }
            else:
                data = {
                    'type': 'no_package'
                }
        elif barcode_product:
            if barcode_product.detailed_type == 'product':
                stock_move = request.env['stock.move'].search([('picking_id', '=', int(pick_id)),
                                                               ('product_id', '=', barcode_product.id)])
                if stock_move:
                    if barcode_product.tracking == 'serial':
                        move_lines_without_serial = stock_move.move_line_ids.filtered(
                            lambda line: not line.lot_name)

                        if move_lines_without_serial:
                            data = {
                                'type': 'exist_product_serial',
                                'id': stock_move.id,
                                'move_lines': stock_move.move_line_ids.read()
                            }
                        else:
                            request.env['stock.move.line'].create({
                                'move_id': stock_move.id,
                                'product_id': barcode_product.id,
                                'quantity': 1,
                                'location_id': stock_move.location_id.id,
                                'location_dest_id': stock_move.location_dest_id.id,
                            })
                            data = {
                                'type': 'exist_product_serial',
                                'id': stock_move.id,
                                'move_lines': stock_move.move_line_ids.read()
                            }

                    elif barcode_product.tracking == 'lot':
                        move_lines_without_lot = stock_move.move_line_ids.filtered(
                            lambda line: not line.lot_name)

                        if move_lines_without_lot:
                            data = {
                                'type': 'exist_product_lot',
                                'id': stock_move.id,
                                'move_lines': stock_move.move_line_ids.read()
                            }
                        else:
                            request.env['stock.move.line'].create({
                                'move_id': stock_move.id,
                                'product_id': barcode_product.id,
                                'quantity': 1,
                                'location_id': stock_move.location_id.id,
                                'location_dest_id': stock_move.location_dest_id.id,
                            })
                            data = {
                                'type': 'exist_product_lot',
                                'id': stock_move.id,
                                'move_lines': stock_move.move_line_ids.read()
                            }

                    else:
                        stock_move.done_quantity += 1
                        stock_move.with_barcode = True
                        data = {
                            'type': 'exist_product',
                            'id': stock_move.id,
                            'quantity': stock_move.done_quantity,
                            'move_lines': stock_move.move_line_ids.read()
                        }
                else:
                    picking = request.env['stock.picking'].browse(int(pick_id))
                    previous_moves_count = len(picking.move_ids_without_package)
                    picking.sudo().write({
                        'move_ids_without_package': [(0, 0, {
                            'product_id': barcode_product.id,
                            'quantity': 1,
                            'done_quantity': 1,
                            'location_id': location_id,
                            'location_dest_id': destination,
                            'name': barcode_product.default_code + ' ' + barcode_product.name if barcode_product.default_code else barcode_product.name,
                        })]
                    })
                    stock_move = picking.move_ids_without_package[-1] if len(
                        picking.move_ids_without_package) > previous_moves_count else None
                    if barcode_product.tracking == 'serial':
                        move_lines_without_serial = stock_move.move_line_ids.filtered(
                            lambda line: not line.lot_name)

                        if move_lines_without_serial:
                            type = 'exist_product_serial'
                        else:
                            type = 'exist_product_serial'

                    elif barcode_product.tracking == 'lot':
                        move_lines_without_lot = stock_move.move_line_ids.filtered(lambda line: not line.lot_name)

                        if move_lines_without_lot:
                            type = 'exist_product_lot'

                        else:
                            type = 'exist_product_lot'

                    else:
                        type = 'product'

                    data = {
                        'type': type,
                        'id': stock_move.id,
                        'image': stock_move.product_id.image_1920,
                        'product_code': stock_move.product_id.default_code,
                        'product_name': stock_move.product_id.name,
                        'quantity': stock_move.done_quantity,
                        'source': stock_move.location_id.complete_name,
                        'source_id': stock_move.location_id.id,
                        'destination': stock_move.location_dest_id.complete_name,
                        'destination_id': stock_move.location_dest_id.id,
                        'product_uom_qty': stock_move.product_uom_qty,
                        'next_serial_number': stock_move.next_serial,
                        'next_serial_count': stock_move.next_serial_count,
                        'tracking': stock_move.product_id.tracking,
                        'operation_type': stock_move.picking_type_id.code,
                        'move_line_ids': stock_move.move_line_ids.read(),
                        'line_quantity': int(
                            sum(stock_move.move_line_ids.filtered(lambda move: move.lot_serial_name)
                                .mapped('quantity'))),
                        'line_quant_int': int(
                            sum(stock_move.move_line_ids.filtered(lambda move: move.lot_serial_name)
                                .mapped('quantity'))),
                    }
            else:
                data = {
                    'type': 'not_storable',
                    'name': barcode_product.name,
                }
        else:
            data = {
                'type': False
            }
        return data

    def get_move_data(self, move_id, show_zero=True):
        """Return formatted stock move data for barcode operations."""
        return {
            'id': move_id.id,
            'res_model': "stock.move",
            'product': move_id.product_id.id,
            'product_name': move_id.product_id.name,
            'image': move_id.product_id.image_1920,
            'product_code': move_id.product_id.default_code,
            'quantity': move_id.quantity if move_id.done_quantity else 0,
            'processed_quantity': move_id.quantity,
            'line_quantity': int(sum(move_id.move_line_ids.filtered(
                lambda move: move.lot_serial_name).mapped('quantity'))) if not show_zero else 0,
            'line_quant_int': int(sum(move_id.move_line_ids.filtered(
                lambda move: move.lot_serial_name).mapped('quantity'))),
            'destination': move_id.location_dest_id.complete_name,
            'source': move_id.location_id.complete_name,
            'source_id': move_id.location_id.id,
            'destination_id': move_id.location_dest_id.id,
            'next_serial_number': move_id.next_serial,
            'next_serial_count': move_id.next_serial_count,
            'product_uom_qty': move_id.product_uom_qty,
            'tracking': move_id.product_id.tracking,
            'operation_type': move_id.picking_type_id.code,
            'move_line_ids': move_id.move_line_ids.read(),
            'lot_name': "",
            'package_name': "",
            'overall_qty': 0

        }

    def get_move_line_data(self, line_id):
        """Return formatted stock move line data for barcode operations."""
        return {
            'id': line_id.id,
            'product': line_id.product_id.id,
            'res_model': "stock.move.line",
            'overall_qty': line_id.move_id.quantity,
            'product_name': line_id.product_id.name,
            'image': line_id.product_id.image_1920,
            'product_code': line_id.product_id.default_code,
            'quantity': line_id.quantity if line_id.move_id.done_quantity else 0,
            'processed_quantity': line_id.quantity,
            'demand_quantity': line_id.move_id.quantity,
            'line_quantity': line_id.quantity,
            'line_quant_int': line_id.quantity,
            'destination': line_id.location_dest_id.complete_name,
            'source': line_id.location_id.complete_name,
            'source_id': line_id.location_id.id,
            'destination_id': line_id.location_dest_id.id,
            'next_serial_number': line_id.move_id.next_serial,
            'next_serial_count': line_id.move_id.next_serial_count,
            'product_uom_qty': line_id.move_id.product_uom_qty,
            'tracking': line_id.product_id.tracking,
            'operation_type': line_id.move_id.picking_type_id.code,
            'lot_name': line_id.lot_id.name,
            'package_name': line_id.result_package_id.name,
            'line_ids': line_id.read(),
        }

    @http.route('/barcode-location/get-product-data', type='json')
    def product_stock_move_barcode(self, pick_id):
        """
        Retrieves product data for stock moves or move lines based on a given picking ID.

        This method fetches product information associated with stock moves or move lines in a stock picking.
        If the picking or specific moves within it are set to use barcode scanning (i.e., `with_barcode` is `True`),
        it retrieves detailed move line data via `get_move_line_data`. Otherwise, it returns general stock move
        data through `get_move_data`.

        Args:
            pick_id (int or str): The ID of the stock picking to retrieve data from, which will be converted to an integer.

        Returns:
            list of dict: A list of dictionaries, where each dictionary contains product data. The returned data depends on
                          whether barcode scanning is enabled at the picking or move level:
                - If `with_barcode` is enabled at the picking level, it returns data for each move line.
                - If `with_barcode` is only enabled on specific moves, it retrieves detailed data for each relevant move line.
                - If barcode scanning is disabled, it retrieves general move data instead.
        """
        picking_id = request.env["stock.picking"].browse(int(pick_id))
        if picking_id.with_barcode:
            return [self.get_move_line_data(line_id) for line_id in
                    request.env['stock.move'].search([('picking_id', '=', int(pick_id))]).mapped("move_line_ids").sorted(key=lambda l: l.write_date)]
        else:
            records = []
            move_ids = request.env['stock.move'].search([('picking_id', '=', int(pick_id))])
            for move_id in move_ids:
                if move_id.with_barcode:
                    for line_id in move_id.move_line_ids:
                        records.append(self.get_move_line_data(line_id))
                else:
                    records.append(self.get_move_data(move_id))

            return records

    @http.route('/barcode-location/product-barcode-confirm', type='json')
    def stock_picking_done(self, pick_id):
        """Call the button_validate method from stock.picking when clicking the confirm button in the barcode transfer view."""
        return request.env['stock.picking'].browse(int(pick_id)).with_context(
            skip_backorder=True, skip_sms=True).button_validate()

    @http.route('/barcode-adjustment/product-barcode', type='json')
    def product_adjustment_barcode(self, code, location):
        """
        Getting data for scanned barcode item from the Barcode products view and
        return the corresponding record in 'stock.quant'.
        """
        barcode_location = request.env['stock.location'].search([('barcode', '=', code)])
        barcode_product = request.env['product.product'].search([('barcode', '=', code)])
        barcode_tracking = request.env['stock.lot'].search([('name', '=', code)])
        if barcode_location:
            data = {
                'type': 'location',
                'name': barcode_location.complete_name,
                'id': barcode_location.id
            }
        elif barcode_product:
            if not location:
                location = request.env['stock.picking.type'].search(
                    [('code', '=', 'incoming'), ('company_id', '=', request.env.company.id)],
                    limit=1).default_location_dest_id.id
            if barcode_product.detailed_type == 'product':
                quant_product = request.env['stock.quant'].search(
                    [('inventory_quantity_set', '=', True), ('created_custom_barcode', '=', True),
                     ('product_id', '=', barcode_product.id), ('location_id', '=', location)])
                quant_product_code = request.env['stock.quant'].search(
                    [('product_id', '=', barcode_product.id), ('location_id', '=', location)])
                if quant_product:
                    quant_product.inventory_quantity += 1
                    data = {
                        'type': 'exist_product',
                        'id': quant_product.id,
                        'quantity': quant_product.inventory_quantity
                    }
                elif quant_product_code and barcode_product.tracking == 'none':
                    quant_product_code.inventory_quantity += 1
                    quant_product_code.created_custom_barcode = True
                    quant_product_code.inventory_quantity_set = True
                    data = {
                        'type': 'product',
                        'id': quant_product_code.id,
                        'quantity': quant_product_code.quantity,
                        'stock_quant': quant_product_code,
                        'location': quant_product_code.location_id.complete_name,
                        'image': quant_product_code.product_id.image_1920,
                        'product': quant_product_code.product_id.id,
                        'product_code': quant_product_code.product_id.default_code,
                        'product_name': quant_product_code.product_id.name,
                        'uom': quant_product_code.product_uom_id.name,
                        'inv_quantity': quant_product_code.inventory_quantity
                    }
                else:
                    location = location if location else request.env['stock.picking.type'].search(
                        [('code', '=', 'incoming'), ('company_id', '=', request.env.company.id)],
                        limit=1).default_location_dest_id.id
                    stock_quant = request.env['stock.quant'].create({
                        'product_id': barcode_product.id,
                        'location_id': location,
                        'quantity': 0,
                        'inventory_quantity': 1,
                        'inventory_diff_quantity': 1,
                        'inventory_quantity_set': True,
                        'created_custom_barcode': True
                    })
                    data = {
                        'type': 'product',
                        'stock_quant': stock_quant,
                        'id': stock_quant.id,
                        'location': stock_quant.location_id.complete_name,
                        'image': stock_quant.product_id.image_1920,
                        'product': stock_quant.product_id.id,
                        'product_code': stock_quant.product_id.default_code,
                        'product_name': stock_quant.product_id.name,
                        'uom': stock_quant.product_uom_id.name,
                        'quantity': stock_quant.quantity,
                        'inv_quantity': stock_quant.inventory_quantity
                    }
            else:
                data = {
                    'type': 'not_storable',
                    'name': barcode_product.name
                }
        elif barcode_tracking:
            if not location:
                location = request.env['stock.picking.type'].search(
                    [('code', '=', 'incoming'), ('company_id', '=', request.env.company.id)],
                    limit=1).default_location_dest_id.id
            if barcode_tracking.product_id.detailed_type == 'product':
                quant_product = request.env['stock.quant'].search(
                    [('inventory_quantity_set', '=', True), ('created_custom_barcode', '=', True),
                     ('product_id', '=', barcode_tracking.product_id.id), ('lot_id', '=', barcode_tracking.id), ('location_id', '=', location)])
                quant_product_code = request.env['stock.quant'].search(
                    [('product_id', '=', barcode_tracking.product_id.id), ('location_id', '=', location)])
                if quant_product:
                    data = {
                        'type': 'exist_product',
                        'id': quant_product.id,
                        'quantity': quant_product.inventory_quantity,
                        'lot_id': barcode_tracking.name,
                        'location_id': quant_product.location_id.complete_name,
                    }
                    if barcode_tracking.product_id.tracking == "serial":
                        data['error'] = True
                    else:
                        quant_product.inventory_quantity += 1
                        data['error'] = False
                elif quant_product_code and barcode_tracking.product_id.tracking == 'none':
                    quant_product_code.inventory_quantity += 1
                    quant_product_code.created_custom_barcode = True
                    quant_product_code.inventory_quantity_set = True
                    data = {
                        'type': 'product',
                        'id': quant_product_code.id,
                        'quantity': quant_product_code.quantity,
                        'stock_quant': quant_product_code,
                        'location': quant_product_code.location_id.complete_name,
                        'image': quant_product_code.product_id.image_1920,
                        'product': quant_product_code.product_id.id,
                        'product_code': quant_product_code.product_id.default_code,
                        'product_name': quant_product_code.product_id.name,
                        'uom': quant_product_code.product_uom_id.name,
                        'inv_quantity': quant_product_code.inventory_quantity
                    }
                else:
                    location = location if location else request.env['stock.picking.type'].search(
                        [('code', '=', 'incoming'), ('company_id', '=', request.env.company.id)],
                        limit=1).default_location_dest_id.id
                    stock_quant = request.env['stock.quant'].create({
                        'product_id': barcode_tracking.product_id.id,
                        'location_id': location,
                        'quantity': 0,
                        'lot_id': barcode_tracking.id,
                        'inventory_quantity': 1,
                        'inventory_diff_quantity': 1,
                        'inventory_quantity_set': True,
                        'created_custom_barcode': True
                    })
                    data = {
                        'type': 'product',
                        'stock_quant': stock_quant,
                        'id': stock_quant.id,
                        'location': stock_quant.location_id.complete_name,
                        'image': stock_quant.product_id.image_1920,
                        'product': stock_quant.product_id.id,
                        'lot_id': stock_quant.lot_id.name,
                        'product_code': stock_quant.product_id.default_code,
                        'product_name': stock_quant.product_id.name,
                        'uom': stock_quant.product_uom_id.name,
                        'quantity': stock_quant.quantity,
                        'inv_quantity': stock_quant.inventory_quantity
                    }
            else:
                data = {
                    'type': 'not_storable',
                    'name': barcode_tracking.product_id.name
                }
        else:
            data = {
                'type': False
            }
        return data

    @http.route('/barcode/batch-barcode', type='json')
    def get_batch_transfer(self, code, id, picking_type, locations):
        """
        Getting data for scanned barcode item from the Barcode batch view and
        return the corresponding record in 'stock.picking.batch'.
        """
        barcode_product = request.env['product.product'].search([('barcode', '=', code)])
        barcode_location = request.env['stock.location'].search([('barcode', '=', code)])
        if barcode_product and locations:

            data = locations
            move_id = request.env['stock.move'].create({
                'picking_id': int(data.get('pick_id')),
                'name': barcode_product.name,
                'location_id': int(data.get('location_id')),
                'location_dest_id': int(data.get('location_dest_id')),
                'product_id': barcode_product.id,
                'product_uom_qty': 1,
                'state': 'assigned',
                'quantity': 1
            })
            request.env['stock.move.line'].create({
                'move_id': move_id.id,
                'picking_id': int(id),
                'quantity_product_uom': move_id.product_uom_qty,
                'product_id': move_id.product_id.id,
                'product_uom_id': move_id.product_uom.id,
                'location_id': move_id.location_id.id,
                'location_dest_id': move_id.location_dest_id.id,
                'state': 'assigned',
                'batch_id': int(id)
            })

            data = {
                'move_line': request.env['stock.move.line'].search_read([
                    ('batch_id', '=', int(id)), ('product_id', '=', barcode_product.id)],
                    ["id", "product_id", "quantity_product_uom", "location_id", "location_dest_id", "picking_id",
                     "quantity_product_uom"])[0],
                'type': 'new_lines'
            } if locations else {'type': 'no_location'}
        elif barcode_location:
            picking_id = request.env['stock.picking'].search([('batch_id', '=', int(id))], limit=1)
            data = {
                'type': 'location',
                'location_id': barcode_location.id if picking_type == 'outgoing' else picking_id.location_id.id,
                'location_dest_id': barcode_location.id if picking_type == 'incoming' else
                picking_id.location_dest_id.id,
                'pick_id': picking_id.id
            }
        else:
            data = False
        return data

    @http.route('/barcode-batch/location-package', type='json')
    def get_group_stock_tracking_lot(self, ):
        """
        Checking if the storage locations and batch is enabled or not.
        """
        return {
            'package': request.env.user.user_has_groups('stock.group_tracking_lot'),
            'location': request.env.user.user_has_groups('stock.group_stock_multi_locations')
        }

    @http.route('/barcode-batch/action_put_in_pack', type='json')
    def action_package(self, id):
        """Call the action_put_in_pack method from stock.picking.batch."""
        return request.env['stock.picking.batch'].browse(int(id)).action_put_in_pack()

    @http.route('/barcode-batch/action_validate', type='json')
    def action_validate(self, id):
        """Call the action_done method from stock.picking.batch."""
        return request.env['stock.picking.batch'].browse(int(id)).action_done()

    @http.route('/barcode-adjustment/get_adjustment_stock_data', type='json')
    def get_adjustment_stock_data(self):
        """
        Function for getting the data for the inventory adjustment
        """
        return [{
            'id': stock.id,
            'location': stock.location_id.complete_name,
            'location_id': stock.location_id.id,
            'image': stock.product_id.image_1920,
            'value': False,
            'product': stock.product_id.id,
            'product_code': stock.product_id.default_code,
            'product_name': stock.product_id.name,
            'uom': stock.product_uom_id.name,
            'quantity': stock.quantity,
            'inv_quantity': stock.inventory_quantity,
        } for stock in request.env['stock.quant'].search(
            ['&', ('inventory_quantity_set', '=', True), ('created_custom_barcode', '=', True), '|',
             ('user_id', '=', request.env.user.id), ('user_id', '=', False)])]

    @http.route('/barcode-adjustment/cancel_stock_quant', type='json')
    def cancel_stock_quant(self, quant_ids):
        """Call the action_clear_inventory_quantity method from stock.quant."""
        request.env['stock.quant'].browse(quant_ids).action_clear_inventory_quantity()
        return True

    @http.route('/barcode-adjustment/apply_multiple_inventory', type='json')
    def apply_multiple_inventory(self, quant_ids):
        """Call the action_apply_inventory method from stock.quant."""
        return request.env['stock.quant'].browse(quant_ids).action_apply_inventory()
