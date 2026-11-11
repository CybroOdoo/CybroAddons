# -*- coding: utf-8 -*-
"""Lots Attachment."""
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import openpyxl

from odoo import fields, models
from odoo.exceptions import UserError, ValidationError


def _get_file_stream(attachment):
    """Return a readable stream of the uploaded binary value."""
    return attachment.open()


class LotsAttachment(models.TransientModel):
    """ Class for lots wizard """
    _name = 'lot.attachment'
    _description = "Lots Attachment"

    picking_id = fields.Many2one('stock.picking',
                                 string="Stock Picking",
                                 help="Parent picking")
    product_id = fields.Many2one('product.product',
                                 help="Current product")
    demanded_quantity = fields.Float(string="Quantity",
                                     help="Product quantity demanded")
    type = fields.Selection(string="Lots Type",
                            selection=[('lot', 'Lot'), ('serial', 'Serial')],
                            help="Choose a lot/serial")
    move_id = fields.Many2one('stock.move')
    attachment = fields.Binary(string="Upload", attachment=True)
    attachment_name = fields.Char(help="Attachment file name")

    def action_import_lot(self):
        """ Importing lots """
        if not self.attachment:
            raise ValidationError(
                self.env._('Check whether you upload the document'))

        current_move_id = self.env['stock.move'].browse(self.move_id.id)
        if not current_move_id.exists():
            raise UserError(self.env._('Stock Move not found.'))

        file_stream = _get_file_stream(self.attachment)
        try:
            wb = openpyxl.load_workbook(filename=file_stream, read_only=True)
            ws = wb.active
            rows = [row for row in ws.iter_rows(min_row=2, values_only=True)
                    if any(row)]
            wb.close()
        except Exception as error:
            raise UserError(self.env._(
                'The uploaded file is not a valid Excel (.xlsx) file. '
                'Please upload an .xlsx file.')) from error

        # Check if product exists in the sheet
        product_name = current_move_id.product_id.display_name
        product_rows = [r for r in rows if len(r) > 1 and r[1] == product_name]
        if not product_rows:
            raise UserError(self.env._(
                'The product "%(product)s" does not exist in the sheet.',
                product=product_name))

        # Read and check the lot name and quantity of every row
        lines = []
        for row in product_rows:
            lot_name = str(row[0]).strip() if row[0] is not None else ''
            if not lot_name:
                raise UserError(self.env._(
                    'A row of the product "%(product)s" has no lot name.',
                    product=product_name))
            raw_quantity = row[2] if len(row) > 2 else None
            if raw_quantity in (None, ''):
                quantity = 1.0
            else:
                try:
                    quantity = float(raw_quantity)
                except (TypeError, ValueError) as error:
                    raise UserError(self.env._(
                        'The quantity "%(quantity)s" of lot "%(lot)s" is '
                        'not a number.',
                        quantity=raw_quantity, lot=lot_name)) from error
            lines.append((lot_name, quantity))

        # Check if a lot name is repeated in the sheet. The existing move
        # lines are replaced by the import, so importing the same sheet
        # again is allowed.
        lot_names = [lot_name for lot_name, _quantity in lines]
        duplicates = sorted({name for name in lot_names
                             if lot_names.count(name) > 1})
        if duplicates:
            raise UserError(self.env._(
                'The lot name(s) %(lots)s appear more than once in the sheet.',
                lots=', '.join(duplicates)))

        # Calculate total sheet quantity for the product
        total_sheet_quantity = sum(quantity for _lot, quantity in lines)

        # Check if total sheet quantity exceeds demand quantity of the product
        if total_sheet_quantity > current_move_id.product_uom_qty:
            raise UserError(self.env._(
                'Total quantity in the sheet exceeds the demand '
                'quantity of the product. Please adjust the quantities '
                'in the sheet.'))

        # Prepare move line values to be written
        vals_list = []
        for lot_name_str, quantity in lines:
            # Search for existing lot
            existing_lot = self.env['stock.lot'].search([
                ('name', '=', lot_name_str),
                ('product_id', '=', current_move_id.product_id.id),
                ('company_id', '=', current_move_id.company_id.id)
            ], limit=1)

            move_line_vals = {
                'quantity': quantity,
                'move_id': current_move_id.id,
                'product_id': current_move_id.product_id.id,
                'picking_id': current_move_id.picking_id.id,
                'location_id': current_move_id.location_id.id,
                'location_dest_id': current_move_id.location_dest_id.id,
            }

            if existing_lot:
                move_line_vals['lot_id'] = existing_lot.id
            else:
                move_line_vals['lot_name'] = lot_name_str

            vals_list.append(fields.Command.create(move_line_vals))

        # Write move line values
        current_move_id.move_line_ids.unlink()
        current_move_id.write({'move_line_ids': vals_list})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_download_sample(self):
        """ For downloading a sample excel file """
        return {
            'type': 'ir.actions.act_url',
            'url': '/download/excel',
            'target': 'self',
            'file_name': 'my_excel_file.xlsx'
        }
