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
import csv
import io
import openpyxl
from odoo import fields, models
from odoo.exceptions import UserError


class ProductImport(models.TransientModel):
    """ Import products with their images from a CSV or XLSX file """
    _name = 'product.import'
    _description = 'Product Import'

    file = fields.Binary(string="Upload File", help="Choose the file to upload")
    file_name = fields.Char(help="Name of the file")
    option = fields.Selection([
        ('csv', 'CSV'),
        ('xlsx', 'XLSX')], default='csv', required=True,
        help="Choose the file type")

    def import_file(self):
        """ Import the products of the uploaded file. Columns: name, type,
        barcode, price and an optional image URL or local path. """
        self.ensure_one()
        if not self.file:
            raise UserError(self.env._("Please upload a file before importing."))
        rows = self._read_csv_rows() if self.option == 'csv' \
            else self._read_xlsx_rows()
        image_failures = []
        for row in rows:
            self._import_row(row, image_failures)
        if not image_failures:
            return None
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._("Import finished, but some images could "
                                    "not be added"),
                'message': "\n".join("- %s (%s): %s" % failure
                                     for failure in image_failures),
                'sticky': True,
                'type': 'warning',
            },
        }

    def _read_csv_rows(self):
        """ Return the data rows of the CSV file, without the header """
        content = bytes(self.file)
        # Files exported from Excel on Windows are frequently cp1252, not
        # UTF-8. 'utf-8-sig' also reads plain UTF-8, and latin-1 maps every
        # byte, so it is the final fallback and cannot fail.
        for encoding in ('utf-8-sig', 'cp1252'):
            try:
                text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = content.decode('latin-1')
        # csv.reader keeps quoted fields with commas (e.g. URLs with query
        # strings) in one column, as RFC 4180 requires.
        return list(csv.reader(io.StringIO(text)))[1:]

    def _read_xlsx_rows(self):
        """ Return the data rows of the active XLSX sheet, without the
        header """
        try:
            book = openpyxl.load_workbook(io.BytesIO(bytes(self.file)),
                                          data_only=True)
        except Exception as e:
            raise UserError(self.env._(
                "Please choose the correct file: %s", e)) from e
        return list(book.active.iter_rows(min_row=2, values_only=True))

    def _import_row(self, row, image_failures):
        """ Create or update the product described by one file row. Image
        errors are added to image_failures instead of stopping the import. """
        if len(row) < 4:
            return
        name, product_type, barcode, price, image_source = [
            str(value).strip() if value is not None else ''
            for value in (list(row) + [None])[:5]]
        if not name:
            return

        Product = self.env['product.template']
        if product_type and product_type not in \
                Product._fields['type'].get_values(self.env):
            raise UserError(self.env._(
                "Invalid product type '%(type)s' for product '%(product)s'.",
                type=product_type, product=name))
        try:
            list_price = float(price) if price else 0.0
        except ValueError as e:
            raise UserError(self.env._(
                "Invalid price '%(price)s' for product '%(product)s'.",
                price=price, product=name)) from e

        vals = {'barcode': barcode or False, 'list_price': list_price}
        if image_source:
            image, reason = Product._get_image_from_source(image_source)
            if image:
                vals['image_1920'] = image
            else:
                image_failures.append((name, image_source, reason))

        product = Product.search([('name', '=', name)], limit=1)
        if product:
            product.write(vals)
        else:
            Product.create(dict(vals, name=name, type=product_type or 'consu'))
