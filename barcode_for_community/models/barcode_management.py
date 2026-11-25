# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, Command, models
from odoo.exceptions import UserError


class BarcodeManagement(models.AbstractModel):
    _name = 'barcode.management'
    _description = 'Barcode Management'

    def search_barcode_in_models(self, barcode, picking_id, batch_id=False):
        """
        Searches for a barcode across specified models and returns relevant details if found.

        This method looks for the given barcode in the models returned by `return_barcode_models`.
        If the barcode is found, it provides details about the barcode, the model in which it was
        found, and the picking type if available. Otherwise, it returns an error message indicating
        that no matching barcode was found.
        """
        picking = False
        if picking_id:
            picking_id = self.env['stock.picking'].browse(picking_id)
            picking = picking_id.picking_type_id.code

        model_and_field = self.return_barcode_models()
        for model, field in model_and_field.items():
            barcode_data = self.env[model].sudo().search([(field, '=', barcode)], limit=1)
            if barcode_data:
                response = {"barcode": barcode, "is_error": False, "message": "barcode scanned",
                            "data": barcode_data.read(), "res_model": model, "operation": False,
                            "picking_type": picking, "product_exist": None, "exist_in_many_picking": False,
                            'exist_picking_ids': []}
                if batch_id:
                    batch_id = self.env['stock.picking.batch'].browse(batch_id)
                    product_exist = []
                    if model == "product.product":
                        product_exist = batch_id.move_line_ids.filtered(
                            lambda rec: rec.product_id.id == barcode_data.id)
                    elif model == "stock.lot":
                        product_exist = batch_id.move_line_ids.filtered(
                            lambda rec: rec.product_id.id == barcode_data.product_id.id)
                    if product_exist:
                        picking_ids = list({rec.picking_id.id for rec in product_exist})
                        response['exist_in_many_picking'] = len(picking_ids) > 1
                        response['exist_picking_ids'] = picking_ids
                    response["product_exist"] = bool(product_exist)
                    response["picking_ids"] = batch_id.picking_ids.ids
                return response
        return {"barcode": barcode, "is_error": True, "message": "barcode scanned, but no barcode found",
                "data": [], "res_model": None, "operation": False, "picking_type": picking, "product_exist": None,
                "exist_in_many_picking": False}

    @api.model
    def return_barcode_models(self):
        """
        Returns a dictionary of models and their fields to search for barcodes,
        based on the current user's access rights.

        This method checks the user’s access rights and includes models relevant
        to stock operations, such as production lots, tracking lots, and locations,
        if the user has the required permissions.
        """
        model_and_field = {
            "product.product": "barcode",
            "stock.picking": "name"
        }
        if self.env.user.has_group('stock.group_production_lot'):
            model_and_field["stock.lot"] = "name"
        if self.env.user.has_group('stock.group_tracking_lot'):
            pkg_model = "stock.package" if "stock.package" in self.env else "stock.quant.package"
            model_and_field[pkg_model] = "name"
        if self.env.user.has_group('stock.group_stock_multi_locations'):
            model_and_field["stock.location"] = "barcode"
        return model_and_field

    def assign_recent_scan(self, res_id, model_name, tracking, product, res_model="stock.picking"):
        """
        Updates the recent scan information on the given record.
        """
        self.env[res_model].browse(res_id).write({
            "barcode_recent_scan": model_name,
            "last_scan_tracking": tracking,
            "last_scanned_product": product
        })

    def _create_move_with_line(self, product, barcode, picking_id):
        """
        Creates a new stock move together with an initial move line for the given product.

        This helper is used when no existing move is found for the product in the picking.
        The move and its first line are both flagged as barcode-scanned.
        """
        return self.env['stock.move'].create({
            "description_picking": product.name,
            "product_id": product.id,
            "product_uom": product.uom_id.id,
            "product_uom_qty": 1,
            "picking_id": picking_id.id,
            "location_id": picking_id.location_id.id,
            "location_dest_id": picking_id.location_dest_id.id,
            "with_barcode": True,
            "move_line_ids": [
                Command.create({
                    "lot_name": barcode,
                    "quantity": 1,
                    "product_id": product.id,
                    "location_id": picking_id.location_id.id,
                    "location_dest_id": picking_id.location_dest_id.id,
                    "is_barcode_scanned": True,
                    "picking_id": picking_id.id
                })
            ]
        })

    def _create_move_line(self, product, picking_id, move_id, barcode):
        """
        Appends a new barcode-scanned move line to an existing stock move.
        """
        move_id.write({
            "with_barcode": True,
            "move_line_ids": [
                Command.create({
                    "lot_name": barcode,
                    "quantity": 1,
                    "product_id": product.id,
                    "location_id": picking_id.location_id.id,
                    "location_dest_id": picking_id.location_dest_id.id,
                    "is_barcode_scanned": True,
                    "picking_id": picking_id.id
                })
            ]
        })

    def _handle_barcode_scan(self, picking_id, barcode, product, move_id=False):
        """
        Handles the barcode scan operation by adding or updating a move line with the scanned product.

        This function checks if there is an existing move for the scanned product or lot/serial number and adds
        or updates the move line accordingly. If the product has serial tracking, it verifies that only one
        quantity is associated with each unique serial number. For lot tracking, it increments the quantity
        of the existing line if a matching lot is found; otherwise, it creates a new move line.
        """
        move_ids = picking_id.move_ids.filtered(lambda p: p.product_id.id == product.id)
        if not picking_id.with_barcode:
            unlinked_move_lines = move_ids.filtered(lambda m: not m.with_barcode).mapped("move_line_ids").filtered(
                lambda line: not line.is_barcode_scanned)
            unlinked_move_lines.unlink()
        if product.tracking == 'serial':
            if not move_ids:
                self._create_move_with_line(product, barcode, picking_id)
            else:
                move_line_ids = move_ids.mapped("move_line_ids")
                line_ids_with_same_barcode = move_line_ids.filtered(
                    lambda line: line.lot_name == barcode) if barcode else []
                if line_ids_with_same_barcode:
                    if len(line_ids_with_same_barcode) == 1 and line_ids_with_same_barcode.quantity == 0:
                        line_ids_with_same_barcode.quantity = 1
                        line_ids_with_same_barcode.is_barcode_scanned = True
                    else:
                        raise UserError(self.env._("There appear to have too many product with the same serial number"))
                else:
                    move_id = move_ids[-1]  # assumes the last line as the default move
                    self._create_move_line(product, picking_id, move_id, barcode)
        elif product.tracking == 'lot':
            if not move_ids:
                self._create_move_with_line(product, barcode, picking_id)
            else:
                move_line_ids = move_ids.mapped("move_line_ids")

                line_ids_with_same_barcode = move_line_ids.filtered(
                    lambda line: line.lot_name == barcode and not line.had_location_by_barcode)
                if line_ids_with_same_barcode:
                    line_id = line_ids_with_same_barcode[-1]
                    line_id.quantity += 1
                else:
                    move_id = move_ids[-1]
                    self._create_move_line(product, picking_id, move_id, barcode)
        else:
            if not move_ids:
                self._create_move_with_line(product, "", picking_id)
            else:
                move_line_ids = move_ids.mapped("move_line_ids").filtered(
                    lambda line: line.lot_name == "" and line.is_barcode_scanned and not line.had_location_by_barcode)
                if move_line_ids:
                    line_id = move_line_ids[-1]
                    line_id.quantity += 1
                else:
                    move_id = move_id or move_ids[-1]
                    self._create_move_line(product, picking_id, move_id, "")

    def _handle_product_scan(self, picking_id, barcode, product):
        """
        Processes a product scan operation by delegating to the barcode scan handler.

        This function is used specifically for product scans, calling `_handle_barcode_scan`
        without a barcode value, as the product itself is scanned directly.
        """
        self._handle_barcode_scan(picking_id, "", product)

    @api.model
    def add_stock_move_line(self, picking_id, **kwargs):
        """
        Adds a stock move line based on a scanned item, either a lot or a product.

        This function takes the picking ID and scanned information and checks if the item
        corresponds to a stock lot or product. It then calls the appropriate handling function
        (`_handle_barcode_scan` for lots, `_handle_product_scan` for products) to add the scanned
        item to the move lines.
        """
        picking_id = self.env["stock.picking"].browse(picking_id)
        res_model = kwargs.get("res_model")
        data, = kwargs.get("data")
        barcode = kwargs.get("barcode")
        product = self.env['product.product']
        if res_model == 'stock.lot':
            product = product.browse(data['product_id'][0])
            self._handle_barcode_scan(picking_id, barcode, product)
        elif res_model == 'product.product':
            product = product.browse(data['id'])
            self._handle_product_scan(picking_id, barcode, product)
        if product:
            self.pre_process_assign_recent_scan(picking_id, res_model, product.tracking, product, **kwargs)

    @api.model
    def add_stock_location_batch(self, pick_ids, **kwargs):
        """
        Assigns stock locations to move lines across multiple pickings in a batch.

        Iterates over the provided picking IDs and delegates to
        `add_stock_location` for each one.
        """
        for picking_id in pick_ids:
            self.add_stock_location(picking_id, **kwargs)

    @api.model
    def add_stock_location(self, picking_id, **kwargs):
        """
        Assigns stock locations to move lines in a stock picking based on the picking type.

        This method updates the source or destination location of move lines within a specified stock picking
        based on the picking type (`incoming`, `outgoing`, or `internal`). It selectively assigns locations
        to move lines that have been scanned via barcode but have not yet had a location assigned by barcode.
        """
        picking_type = kwargs.get('picking_type')
        data, = kwargs.get('data')
        picking_id = self.env['stock.picking'].browse(picking_id)
        if not picking_type:
            picking_type = picking_id.picking_type_id.code
        move_line_ids = picking_id.move_ids.mapped("move_line_ids").filtered(
            lambda line: line.is_barcode_scanned)
        move_line_ids_without_location = move_line_ids.filtered(lambda line: not line.had_location_by_barcode)
        if picking_type == "incoming":
            for line_id in move_line_ids_without_location:
                line_id.location_dest_id = data['id']
                line_id.had_location_by_barcode = True
        elif picking_type == "outgoing":
            for line_id in move_line_ids_without_location:
                line_id.location_id = data['id']
                line_id.had_location_by_barcode = True
        elif picking_type == "internal":
            for line_id in move_line_ids:
                if not line_id.had_location_by_barcode and not line_id.had_location_by_barcode_dest:
                    line_id.location_id = data['id']
                    line_id.had_location_by_barcode = True
                elif line_id.had_location_by_barcode and not line_id.had_location_by_barcode_dest:
                    line_id.location_dest_id = data['id']
                    line_id.had_location_by_barcode_dest = True

        res_model = kwargs.get("res_model")
        self.pre_process_assign_recent_scan(picking_id, res_model, "", False, **kwargs)

    def create_lot(self, code, prod_id):
        """
        Creates a new stock lot with the given name and product.
        """
        return self.env['stock.lot'].create({
            'name': code,
            'product_id': prod_id
        })

    def assign_lot_number(self, picking_id, lot_id, product_id):
        """
        Assigns a lot/serial record to the latest unassigned barcode-scanned move line.

        Finds move lines within the picking that were created via barcode and do not
        yet have a lot assigned, then writes the provided lot onto the last such line.
        """
        move_ids = picking_id.move_ids.filtered(lambda p: p.product_id.id == product_id)
        line_ids = move_ids.mapped("move_line_ids").filtered(
            lambda line: line.is_barcode_scanned and not line.lot_id)
        if line_ids:
            line_id = line_ids[-1]
            line_id.write({
                "lot_id": lot_id.id,
                "lot_name": lot_id.name,
            })

    @api.model
    def assign_barcode_move_line(self, picking_id, product_id, **kwargs):
        """
        Assigns a lot or serial number to a move line in a stock picking record based on barcode data.

        This method checks the stock picking's configuration for handling lots/serial numbers and assigns
        a lot (or serial number) to a move line within the specified picking (`picking_id`). It verifies if
        the lot (or serial) already exists based on the provided `barcode`. Depending on the configuration,
        it may create a new lot or raise an error if it cannot assign the lot.
        """
        picking_id = self.env['stock.picking'].browse(picking_id)
        picking_type_id = picking_id.picking_type_id
        barcode = kwargs.get('barcode')
        existing_lots = self.env['stock.lot'].search([('name', '=', barcode)], limit=1)
        lot_id = existing_lots
        if picking_type_id.use_create_lots and picking_type_id.use_existing_lots:
            if not existing_lots:
                lot_id = self.create_lot(barcode, product_id)
        elif picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
            if existing_lots:
                raise UserError(self.env._("Existing Serial/lots cannot be assigned."))
            else:
                lot_id = self.create_lot(barcode, product_id)
        elif not picking_type_id.use_create_lots and picking_type_id.use_existing_lots:
            if not existing_lots:
                raise UserError(self.env._("New Serial/lots cannot be assigned."))
        else:
            raise UserError(self.env._("Please enable Use Create Lots or use existing lots before assigning Barcodes."))
        if lot_id:
            self.assign_lot_number(picking_id, lot_id, product_id)

        res_model = kwargs.get("res_model")
        self.pre_process_assign_recent_scan(picking_id, res_model, "", False, **kwargs)

    @api.model
    def assign_package_move_line_batch(self, pick_ids, **kwargs):
        """
        Assigns a package to move lines across multiple pickings in a batch.

        Iterates over the provided picking IDs and delegates to
        `assign_package_move_line` for each one.
        """
        for picking_id in pick_ids:
            self.assign_package_move_line(picking_id, **kwargs)

    @api.model
    def assign_package_move_line(self, picking_id, **kwargs):
        """
        Assigns a package to move lines in a stock picking record.

        This method assigns a package to available move lines within the specified stock picking (`picking_id`).
        It ensures that the package is not already in use by filtering out any move lines that already have
        the package assigned, preventing reuse. If no move lines are available without a package,
        it prompts the user to scan at least one new product.
        """
        data, = kwargs.get('data')
        picking_id = self.env['stock.picking'].browse(picking_id)
        line_ids = picking_id.move_ids.mapped("move_line_ids").filtered(
            lambda line: line.quantity)
        if picking_id.picking_type_id.code == "incoming":
            line_ids = line_ids.filtered(lambda line: not line.had_location_by_barcode)
        elif picking_id.picking_type_id.code == "internal":
            line_ids = line_ids.filtered(lambda line: not line.had_location_by_barcode_dest)
        elif picking_id.picking_type_id.code == "outgoing":
            line_ids = line_ids
        if line_ids.filtered(lambda line: line.result_package_id.id == data.get('id')):
            raise UserError(self.env._("Can't Reuse the package."))
        else:
            line_ids = line_ids.filtered(lambda line: not line.result_package_id)
            if not line_ids:
                raise UserError(self.env._("Please Scan at least one new product before scanning package."))
            else:
                for line in line_ids:
                    line.result_package_id = data.get("id")

        res_model = kwargs.get("res_model")
        self.pre_process_assign_recent_scan(picking_id, res_model, "", False, **kwargs)

    def pre_process_assign_recent_scan(self, picking_id, response_model, tracking, product, **kwargs):
        """
        Pre-processes arguments and delegates to `assign_recent_scan`.

        Resolves the correct record model and ID from kwargs—using the batch
        model when applicable—before calling `assign_recent_scan`.
        """
        rec_model = kwargs.get("rec_model")
        rec_model_id = kwargs.get("rec_model_id")
        rec_id = rec_model_id if rec_model == "stock.picking.batch" else picking_id.id
        rec_model = rec_model or 'stock.picking'
        self.assign_recent_scan(rec_id, response_model, tracking, product, rec_model)

    @api.model
    def action_remove_move_line(self, picking_id, line_id, res_model):
        """
        Removes a stock move or move line by its ID and resets the recent scan state.
        """
        if res_model in ['stock.move.line', 'stock.move']:
            self.env[res_model].browse(line_id).unlink()
        self.assign_recent_scan(picking_id, "", "", False)

    @api.model
    def add_move_line_by_one(self, move_id):
        """
        Increments the quantity of an existing stock move line by one unit via barcode scan.

        Looks up the move by ID, resolves its product and picking, then delegates
        to `_handle_barcode_scan` to add or update the move line by one.
        """
        move_id = self.env["stock.move"].browse(move_id)
        product_id = move_id.product_id
        picking_id = move_id.picking_id
        self._handle_barcode_scan(picking_id, "", product_id, move_id)
