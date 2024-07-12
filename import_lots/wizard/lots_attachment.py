# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models
from odoo import _
from odoo.exceptions import UserError, ValidationError
import openpyxl
import base64
from io import BytesIO


class LotsAttachment(models.TransientModel):
    """Class for lots wizard"""
    _name = 'lot.attachment'
    _description = "Lots Attachment"

    picking_id = fields.Many2one('stock.picking',
                                 string="Stock Picking",
                                 help="Parent picking")
    product_id = fields.Many2one('product.product',
                                 string="Product",
                                 help="Current product")
    demanded_quantity = fields.Float(string="Quantity",
                                     help="Product quantity demanded")
    type = fields.Selection(string="Lots Type",
                            selection=[('lot', 'Lot'), ('serial', 'Serial')],
                            help="Choose a lot/serial")
    move_id = fields.Many2one('stock.move', string="Stock Move",
                              help="Relation to stock_move")
    attachment = fields.Binary(string="Upload",
                               help="Attach your file to import")

    def import_lot(self):
        """Importing lots"""
        current_move_id = self.env['stock.move'].browse(self.move_id.id)
        wb = openpyxl.load_workbook(
            filename=BytesIO(base64.b64decode(self.attachment)), read_only=True) \
            if self.attachment else ""
        if not wb:
            raise ValidationError(_('Check whether you upload the document'))
        ws = wb.active
        # Check if product exists in the sheet
        product_found = any(
            record[1] == current_move_id.product_id.display_name for record in
            ws.iter_rows(min_row=2, values_only=True))
        if not product_found:
            raise UserError(
                _('The product "%s" does not exist in the sheet.') %
                current_move_id.product_id.display_name)
        # Check if lot name already exists in move line ids
        if current_move_id.move_line_ids and any(record[0] in set(
                current_move_id.move_line_ids.mapped('lot_name')) for record in
                                                 ws.iter_rows(min_row=2,
                                                              values_only=True)):
            raise UserError(
                _('This Lot name already exists in the move line.'))
        # Calculate total sheet quantity for the product
        total_sheet_quantity = sum(
            record[2] for record in ws.iter_rows(min_row=2, values_only=True) if
            record[1] == current_move_id.product_id.display_name)
        # Check if total sheet quantity exceeds demand quantity of the product
        if total_sheet_quantity > current_move_id.product_uom_qty:
            raise UserError(
                _('Total quantity in the sheet exceeds the demand quantity of '
                  'the product. Please adjust the quantities in the sheet.'))
        # Prepare move line values to be written
        vals_list = []
        for record in ws.iter_rows(min_row=2, values_only=True):
            lot_name, product_name, quantity = record
            if product_name == current_move_id.product_id.display_name:
                vals_list.append((0, 0, {
                    'lot_name': lot_name,
                    'qty_done': min(quantity, current_move_id.product_qty),
                    'move_id': current_move_id.id,
                    'product_uom_id': current_move_id.product_uom.id,
                    'location_id': current_move_id.location_id.id,
                    'location_dest_id': current_move_id.location_dest_id.id,
                }))
        # Write move line values
        current_move_id.move_line_ids.unlink()
        current_move_id.write({'move_line_ids': vals_list})
        if self.picking_id.show_reserved:
            view = self.env.ref('stock.view_stock_move_operations')
        else:
            view = self.env.ref('stock.view_stock_move_nosuggest_operations')
        return {
            'name': _('Detailed Operations'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'views': [(view.id, 'form')],
            'view_id': self.env.ref('stock.view_stock_move_operations').id,
            'target': 'new',
            'res_id': self.move_id.id,
            'context': {
                'default_move_line_ids': current_move_id.move_line_ids.ids,
                'show_lots_text': True
            },
        }

    def download_excel_file(self):
        """For downloading a sample excel file"""
        return {
            'type': 'ir.actions.act_url',
            'url': '/download/excel',
            'target': 'self',
            'file_name': 'my_excel_file.xlsx'
        }
