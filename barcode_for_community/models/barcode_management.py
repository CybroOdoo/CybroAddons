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
from odoo import api, models, Command
from odoo.exceptions import UserError


class BarcodeManagement(models.AbstractModel):
    """
    Abstract model containing barcode scanning logic and utility methods for inventory operations.
    """
    _name = 'barcode.management'
    _description = 'Barcode Management'

    def search_barcode_in_models(self, barcode, picking_id, batch_id=False):
        """
        Searches for a barcode across specified models and returns relevant details if found.

        This method looks for the given barcode in the models returned by `return_barcode_models`.
        If the barcode is found, it provides details about the barcode, the model in which it was
        found, and the picking type if available. Otherwise, it returns an error message indicating
        that no matching barcode was found.

        Args:
            barcode (str): The scanned barcode to search for across models.
            picking_id (int): The ID of the picking operation associated
                                        with the barcode, if applicable.
            batch_id (int) Optional: The ID of the batch transfer.

        Returns:
            dict: A dictionary containing:
                - "barcode" (str): The scanned barcode.
                - "is_error" (bool): False if barcode is found, otherwise True.
                - "message" (str): A message indicating the scan result.
                - "data" (list): A list containing the found barcode data, if any.
                - "res_model" (str or None): The model in which the barcode was found.
                - "operation" (bool): Default False, can be customized for future needs.
                - "picking_type" (str or None): The type of picking operation, if available.
                - "product_exist" (bool or None): Whether the product exists in batch.
                - "exist_in_many_picking" (bool or False): Whether the product exists in multiple picking.
                - "exist_picking_ids" (array): picking ids where the scanned product exist.
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

        Returns:
            dict: A dictionary where the key is the model name and the value is the field
                  name containing the barcode information.
        """
        model_and_field = {
            "product.product": "barcode",
            "stock.picking": "name"
        }
        if self.env.user.has_group('stock.group_production_lot'):
            model_and_field["stock.lot"] = "name"
        if self.env.user.has_group('stock.group_tracking_lot'):
            model_and_field["stock.quant.package"] = "name"
        if self.env.user.has_group('stock.group_stock_multi_locations'):
            model_and_field["stock.location"] = "barcode"
        return model_and_field

    def assign_recent_scan(self, res_id, model_name, tracking, product, res_model="stock.picking"):
        """Assign the latest scanned barcode data to the corresponding picking or batch record."""
        self.env[res_model].browse(res_id).write({
            "barcode_recent_scan": model_name,
            "last_scan_tracking": tracking,
            "last_scanned_product": product
        })

    def _create_move_with_line(self, product, barcode, picking_id):
        """Create a new stock move and an associated move line with barcode information."""
        move_id = self.env['stock.move'].create({
            'name': product.name,
            "product_id": product.id,
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
        picking_id.write({
            "move_ids_without_package": [Command.link(move_id.id)],
        })

    def _create_move_line(self, product, picking_id, move_id, barcode):
        """Create a new stock move line within an existing stock move."""
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

        Args:
            picking_id (record): The stock picking record where the product should be added.
            barcode (str): The scanned barcode or serial/lot number.
            product (record): The product being scanned.
            move_id (record) Optional: The move of the operation

        Raises:
            UserError: If there are multiple products with the same serial number.
        """
        move_ids = picking_id.move_ids_without_package.filtered(lambda p: p.product_id.id == product.id)
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
                        raise UserError("There appear to have too many product with the same serial number")
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

        Args:
            picking_id (record): The stock picking record to which the product should be added.
            barcode (str): The barcode or serial/lot number of the product.
            product (record): The product record that has been scanned.
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

        Args:
            picking_id (int): The ID of the stock picking record to which the item should be added.
            **kwargs: Additional arguments, including:
                - res_model (str): The model of the scanned item ('stock.lot' or 'product.product').
                - data (dict): Contains information about the item being scanned.
                - barcode (str): The scanned barcode or lot/serial number of the item.
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
        """Assign stock locations to move lines for multiple stock pickings in a batch."""
        for picking_id in pick_ids:
            self.add_stock_location(picking_id, **kwargs)

    @api.model
    def add_stock_location(self, picking_id, **kwargs):
        """
        Assigns stock locations to move lines in a stock picking based on the picking type.

        This method updates the source or destination location of move lines within a specified stock picking
        based on the picking type (`incoming`, `outgoing`, or `internal`). It selectively assigns locations
        to move lines that have been scanned via barcode but have not yet had a location assigned by barcode.

        Args:
            picking_id (int): The ID of the stock picking to which locations will be assigned.
            kwargs (dict): Additional arguments including:
                - picking_type (str): Type of picking operation, can be "incoming", "outgoing", or "internal".
                - data (dict): Location data dictionary, expected to contain:
                    - 'id' (int): The ID of the stock location to be assigned.
                - res_model (str, optional): Name of the model for the recent scan assignment.

        Raises:
            UserError: If an attempt is made to reassign a destination location in an internal picking.

        Usage:
            Depending on the picking type, the following actions are performed:
            - **incoming**: Assigns `location_dest_id` to move lines without a location, marking them as
              having a location by barcode.
            - **outgoing**: Sets the `location_id` on move lines without a location and marks them accordingly.
            - **internal**: Manages both source and destination locations, only allowing assignment
              if the line has not already had a destination assigned.

        Returns:
            None
        """
        picking_type = kwargs.get('picking_type')
        data, = kwargs.get('data')
        picking_id = self.env['stock.picking'].browse(picking_id)
        if not picking_type:
            picking_type = picking_id.picking_type_id.code
        move_line_ids = picking_id.move_ids_without_package.mapped("move_line_ids").filtered(
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
                    temp = True
                elif line_id.had_location_by_barcode and not line_id.had_location_by_barcode_dest:
                    line_id.location_dest_id = data['id']
                    line_id.had_location_by_barcode_dest = True
                    temp = True

        res_model = kwargs.get("res_model")
        self.pre_process_assign_recent_scan(picking_id, res_model, "", False, **kwargs)

    def create_lot(self, code, prod_id):
        """Create a new stock lot with the specified code and product ID."""
        return self.env['stock.lot'].create({
            'name': code,
            'product_id': prod_id
        })

    def assign_lot_number(self, picking_id, lot_id, product_id):
        """Assign a lot number to the first scanned move line of a product that lacks a lot."""
        move_ids_without_package = picking_id.move_ids_without_package.filtered(lambda p: p.product_id.id == product_id)
        line_ids = move_ids_without_package.mapped("move_line_ids").filtered(
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

        Args:
            picking_id (int): ID of the stock picking to which the lot/serial should be assigned.
            product_id (int): ID of the product being scanned for assignment.
            kwargs (dict): Additional arguments, which must contain:
                - barcode (str): Barcode of the lot/serial number. Used to find or create a `stock.lot` record.
                  This data should match the structure expected in `stock.lot` to perform lot lookups and
                  assignments correctly.

        Raises:
            UserError: If existing lots cannot be assigned (based on picking type configuration).
            UserError: If new lots cannot be assigned (based on picking type configuration).
            UserError: If neither 'use_create_lots' nor 'use_existing_lots' is enabled on the picking type.

        Returns:
            None
        """
        picking_id = self.env["stock.picking"].browse(picking_id)
        picking_type_id = picking_id.picking_type_id
        barcode = kwargs.get('barcode')
        existing_lots = self.env['stock.lot'].search([('name', '=', barcode)], limit=1)
        lot_id = existing_lots
        if picking_type_id.use_create_lots and picking_type_id.use_existing_lots:
            if not existing_lots:
                lot_id = self.create_lot(barcode, product_id)
        elif picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
            if existing_lots:
                raise UserError("Existing Serial/lots cannot be assigned.")
            lot_id = self.create_lot(barcode, product_id)
        elif not picking_type_id.use_create_lots and picking_type_id.use_existing_lots:
            if not existing_lots:
                raise UserError("New Serial/lots cannot be assigned.")
        else:
            raise UserError("Please enable Use Create Lots or use existing lots before assigning Barcodes.")
        if lot_id:
            self.assign_lot_number(picking_id, lot_id, product_id)

        res_model = kwargs.get("res_model")
        self.pre_process_assign_recent_scan(picking_id, res_model, "", False, **kwargs)

    @api.model
    def assign_package_move_line_batch(self, pick_ids, **kwargs):
        """Assign a package to move lines for multiple stock pickings in a batch."""
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

        Args:
            picking_id (int): ID of the stock picking to which the package should be assigned.
            kwargs (dict): Additional arguments, which must contain:
                - data (dict): Information of a `stock.quant.package` record, with the following keys:
                    - 'id' (int): ID of the package to be assigned.
                - res_model (str, optional): Name of the model for which the recent scan should be assigned.

        Raises:
            UserError: If the package is already assigned to a line in the picking.
            UserError: If no available move lines are found to assign the package.

        Returns:
            None
        """
        data, = kwargs.get('data')
        picking_id = self.env['stock.picking'].browse(picking_id)
        line_ids = picking_id.move_ids_without_package.mapped("move_line_ids").filtered(
            lambda line: line.quantity)
        if picking_id.picking_type_id.code == "incoming":
            line_ids = line_ids.filtered(lambda line: not line.had_location_by_barcode)
        elif picking_id.picking_type_id.code == "internal":
            line_ids = line_ids.filtered(lambda line: not line.had_location_by_barcode_dest)
        if line_ids.filtered(lambda line: line.result_package_id.id == data.get('id')):
            raise UserError("Can't Reuse the package.")
        line_ids = line_ids.filtered(lambda line: not line.result_package_id)
        if not line_ids:
            raise UserError("Please Scan at least one new product before scanning package.")
        for line in line_ids:
            line.result_package_id = data.get("id")

        res_model = kwargs.get("res_model")
        self.pre_process_assign_recent_scan(picking_id, res_model, "", False, **kwargs)

    def pre_process_assign_recent_scan(self, picking_id, response_model, tracking, product, **kwargs):
        """Determine whether the target record is a picking or batch and update its recent scan details."""
        rec_model = kwargs.get("rec_model")
        rec_model_id = kwargs.get("rec_model_id")
        rec_id = rec_model_id if rec_model == "stock.picking.batch" else picking_id.id
        rec_model = rec_model or 'stock.picking'
        self.assign_recent_scan(rec_id, response_model, tracking, product, rec_model)

    @api.model
    def action_remove_move_line(self, picking_id, line_id, res_model):
        """Unlink the specified move line or move and reset the recent scan info on the picking."""
        if res_model in ['stock.move.line', 'stock.move']:
            self.env[res_model].browse(line_id).unlink()
        self.assign_recent_scan(picking_id, "", "", False)

    @api.model
    def add_move_line_by_one(self, move_id):
        """Increment the quantity of the stock move by adding a new move line."""
        move_id = self.env["stock.move"].browse(move_id)
        product_id = move_id.product_id
        picking_id = move_id.picking_id
        self._handle_barcode_scan(picking_id, "", product_id, move_id)
