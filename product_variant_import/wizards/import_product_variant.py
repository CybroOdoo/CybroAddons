# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import os
import base64, binascii, csv, io, tempfile, requests, xlrd
from odoo import fields, models, _
from odoo.exceptions import UserError


class ImportVariant(models.TransientModel):
    """Wizard for selecting the imported Files"""
    _name = 'import.product.variant'
    _description = "Import Product Variants"

    import_file = fields.Selection(
        [('csv', 'CSV File'), ('excel', 'Excel File')], required=True,
        string="Import FIle", help="Import the files")
    method = fields.Selection([('create', 'Create Product'),
                               ('update', 'Update Product'), (
                                   'update_product',
                                   'Update Product Variant'), ],
                              string="Method", required=True,
                              help="Method for importing/Exporting")
    file = fields.Binary(string="File", required=True,
                         help="The file to upload")

    def action_import_product_variant(self):
        """This is used to import/export the product"""
        try:
            if self.import_file == 'excel':
                # Handle Excel file
                try:
                    file_pointer = tempfile.NamedTemporaryFile(delete=False,
                                                               suffix=".xlsx")
                    file_pointer.write(binascii.a2b_base64(self.file))
                    file_pointer.seek(0)

                    book = xlrd.open_workbook(file_pointer.name)
                    sheet = book.sheet_by_index(0)

                    if sheet.nrows < 2:
                        raise UserError(
                            _("Excel file is empty or contains only headers"))

                    headers = [str(cell.value).strip() for cell in sheet.row(0)]

                    for row_index in range(1, sheet.nrows):
                        row = sheet.row(row_index)
                        values = {}

                        for col_index, cell in enumerate(row):
                            if col_index < len(headers):
                                cell_value = cell.value
                                if isinstance(cell_value,
                                              str) and cell_value.replace('.',
                                                                          '').isdigit():
                                    try:
                                        cell_value = float(cell_value)
                                    except ValueError:
                                        pass
                                values[headers[col_index]] = cell_value

                        if not values.get(
                                'Internal Reference') and not values.get(
                            'Barcode'):
                            raise UserError(
                                _("Row %d: Must contain either Internal Reference or Barcode") % row_index)

                        vals = {
                            'name': values.get('Name'),
                            'default_code': str(
                                values.get('Internal Reference', '')).strip(),
                            'barcode': str(values.get('Barcode', '')).strip(),
                            'sale_ok': str(
                                values.get('Can be sold', 'True')).lower() in (
                                           'true', 't', '1', 'yes'),
                            'purchase_ok': str(
                                values.get('Purchase_ok', 'True')).lower() in (
                                               'true', 't', '1', 'yes'),
                        }

                        if values.get('Category'):
                            category = self._get_or_create_category(
                                str(values['Category']))
                            vals['categ_id'] = category

                        if values.get('Unit of Measure'):
                            uom = self._get_uom(str(values['Unit of Measure']))
                            vals['uom_id'] = uom

                        if values.get('Purchase Unit of Measure'):
                            po_uom = self._get_uom(
                                str(values['Purchase Unit of Measure']))
                            vals['uom_po_id'] = po_uom

                        if values.get('Description for customers'):
                            vals['description_sale'] = str(
                                values['Description for customers'])

                        numeric_fields = {
                            'Sales Price': 'list_price',
                            'Cost': 'standard_price',
                            'Weight': 'weight',
                            'Volume': 'volume'
                        }

                        for excel_field, odoo_field in numeric_fields.items():
                            if values.get(excel_field):
                                try:
                                    if isinstance(values[excel_field],
                                                  (int, float)):
                                        vals[odoo_field] = float(
                                            values[excel_field])
                                    else:
                                        vals[odoo_field] = float(
                                            str(values[excel_field]).replace(
                                                ',', ''))
                                except ValueError:
                                    raise UserError(_(
                                        "Row %d: Invalid numeric value for %s: %s"
                                    ) % (row_index, excel_field,
                                         values[excel_field]))

                        if values.get('Customer Taxes'):
                            customer_tax = self._get_or_create_tax(
                                str(values['Customer Taxes']))
                            if customer_tax:
                                vals['taxes_id'] = [(6, 0, [customer_tax])]

                        if values.get('Vendor Taxes'):
                            vendor_tax = self._get_or_create_tax(
                                str(values['Vendor Taxes']))
                            if vendor_tax:
                                vals['supplier_taxes_id'] = [
                                    (6, 0, [vendor_tax])]

                        if values.get('Product Type'):
                            product_type = self._get_selection_field_value(
                                'detailed_type', str(values['Product Type']))
                            if product_type:
                                vals['detailed_type'] = product_type

                        if values.get('Invoicing Policy'):
                            invoice_policy = self._get_selection_field_value(
                                'invoice_policy',
                                str(values['Invoicing Policy']))
                            if invoice_policy:
                                vals['invoice_policy'] = invoice_policy

                        if self.method == 'create':
                            product = self.env['product.template'].create(vals)
                        else:
                            product = self._update_existing_product(vals,
                                                                    values)

                        if values.get('Variant Attributes') and values.get(
                                'Attribute Values'):
                            variant_attrs = str(values['Variant Attributes'])
                            variant_values = str(values['Attribute Values'])
                            self._create_product_variants(product, {
                                'Variant Attributes': variant_attrs,
                                'Attribute Values': variant_values
                            })

                    os.unlink(file_pointer.name)

                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Success'),
                            'message': _(
                                'Products imported successfully from Excel file'),
                            'type': 'success',
                            'sticky': False,
                        }
                    }

                except xlrd.XLRDError:
                    raise UserError(
                        _("Invalid Excel file format. Please make sure you're using a valid .xlsx file"))
                except Exception as e:
                    raise UserError(
                        _("Error processing Excel file: %s") % str(e))

            elif self.import_file == 'csv':
                if self.import_file == 'csv':
                    try:
                        files = base64.b64decode(self.file)
                        data = io.StringIO(files.decode("utf-8"))
                        data.seek(0)
                        file_reader = []
                        csv_reader = csv.reader(data, delimiter=',')
                        file_reader.extend(csv_reader)
                    except:
                        raise UserError(
                            _("Invalid file format. Please check your CSV file."))

                    if len(file_reader) < 2:
                        raise UserError(
                            _("File is empty or contains only headers"))

                    header = file_reader[0]

                    for row_index, row in enumerate(file_reader[1:], 1):
                        try:
                            values = {}
                            for i, cell in enumerate(row):
                                if i < len(
                                        header):
                                    values[header[i]] = cell

                            if not values.get(
                                    'Internal Reference') and not values.get(
                                'Barcode'):
                                raise UserError(
                                    _("Row %d: Must contain either Internal Reference or Barcode") % row_index)

                            vals = {
                                'name': values.get('Name'),
                                'default_code': values.get(
                                    'Internal Reference'),
                                'barcode': values.get('Barcode'),
                                'sale_ok': values.get('Can be sold',
                                                      'True').lower() in (
                                               'true', 't', '1', 'yes'),
                                'purchase_ok': values.get('Purchase_ok',
                                                          'True').lower() in (
                                                   'true', 't', '1', 'yes'),
                                'categ_id': self._get_or_create_category(
                                    values.get('Category', '')),
                                'uom_id': self._get_uom(
                                    values.get('Unit of Measure')),
                                'uom_po_id': self._get_uom(
                                    values.get('Purchase Unit of Measure')),
                                'description_sale': values.get(
                                    'Description for customers'),
                            }

                            for field, value in [
                                ('list_price', values.get('Sales Price')),
                                ('standard_price', values.get('Cost')),
                                ('weight', values.get('Weight')),
                                ('volume', values.get('Volume'))
                            ]:
                                try:
                                    if value:
                                        vals[field] = float(value)
                                except ValueError:
                                    raise UserError(
                                        _("Row %d: Invalid numeric value for %s: %s") %
                                        (row_index, field, value))

                            customer_tax = self._get_or_create_tax(
                                values.get('Customer Taxes', ''))
                            vendor_tax = self._get_or_create_tax(
                                values.get('Vendor Taxes', ''))

                            if customer_tax:
                                vals['taxes_id'] = [(6, 0, [customer_tax])]
                            if vendor_tax:
                                vals['supplier_taxes_id'] = [
                                    (6, 0, [vendor_tax])]

                            if values.get('Product Type'):
                                product_type = self._get_selection_field_value(
                                    'detailed_type',
                                    values['Product Type'])
                                if product_type:
                                    vals['detailed_type'] = product_type

                            if values.get('Invoicing Policy'):
                                invoice_policy = self._get_selection_field_value(
                                    'invoice_policy',
                                    values['Invoicing Policy'])
                                if invoice_policy:
                                    vals['invoice_policy'] = invoice_policy

                            if values.get('image'):
                                image_data = self._process_image(
                                    values['image'])
                                if image_data:
                                    vals['image_1920'] = image_data

                            if self.method == 'create':
                                product = self.env['product.template'].create(
                                    vals)
                            else:
                                product = self._update_existing_product(vals,
                                                                        values)

                            if values.get('Variant Attributes') and values.get(
                                    'Attribute Values'):
                                self._create_product_variants(product, values)

                        except Exception as e:
                            raise UserError(_("Error processing row %d: %s") % (
                                row_index, str(e)))

                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Success'),
                            'message': _('Products imported successfully'),
                            'type': 'success',
                            'sticky': False,
                        }
                    }

                pass

        except Exception as e:
            raise UserError(str(e))

    def _get_or_create_category(self, category_name):
        """Get existing category or create new one"""
        if not category_name:
            return self.env.ref('product.product_category_all').id

        category = self.env['product.category'].search(
            [('name', '=', category_name)], limit=1)
        if not category:
            category = self.env['product.category'].create(
                {'name': category_name})
        return category.id

    def _get_uom(self, uom_name):
        """Get UoM by name"""
        if not uom_name:
            return self.env.ref('uom.product_uom_unit').id

        uom = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)
        if not uom:
            raise UserError(_("Invalid UoM: %s") % uom_name)
        return uom.id

    def _get_or_create_tax(self, tax_string):
        """Get existing tax or create new one"""
        if not tax_string or not tax_string.strip():
            return False

        try:
            tax = self.env['account.tax'].search([('name', '=', tax_string)],
                                                 limit=1)
            if tax:
                return tax.id

            if ' ' in tax_string:
                parts = tax_string.rsplit(' ',
                                          1)
                if len(parts) == 2:
                    name, amount = parts
                    try:
                        amount = float(
                            amount.replace('%', ''))
                        tax = self.env['account.tax'].create({
                            'name': name,
                            'amount': amount,
                            'type_tax_use': 'sale'
                        })
                        return tax.id
                    except ValueError:
                        tax = self.env['account.tax'].create({
                            'name': tax_string,
                            'amount': 0.0,
                            'type_tax_use': 'sale'
                        })
                        return tax.id

            tax = self.env['account.tax'].create({
                'name': tax_string,
                'amount': 0.0,
                'type_tax_use': 'sale'
            })
            return tax.id
        except Exception as e:
            raise UserError(
                _("Error processing tax '%s': %s") % (tax_string, str(e)))




    def _get_selection_field_value(self, field_name, value):
        """Get the technical value for selection fields"""
        if not value:
            return False

        field = self.env['product.template']._fields[field_name]
        for key, val in field.selection:
            if val == value:
                return key
        return False

    def _process_image(self, image_path):
        """Process image from URL or file path"""
        try:
            if image_path.startswith(('http://', 'https://')):
                response = requests.get(image_path.strip())
                return base64.b64encode(response.content)
            elif os.path.exists(image_path):
                with open(image_path, 'rb') as image_file:
                    return base64.b64encode(image_file.read())
            return False
        except:
            return False

    def _update_existing_product(self, vals, values):
        """Update existing product based on reference or barcode"""
        product = False
        if values.get('Barcode'):
            product = self.env['product.template'].search(
                [('barcode', '=', values['Barcode'])], limit=1)
        if not product and values.get('Internal Reference'):
            product = self.env['product.template'].search(
                [('default_code', '=', values['Internal Reference'])], limit=1)

        if not product:
            raise UserError(
                _("No product found with the given barcode or internal reference"))

        product.write(vals)
        return product

    def _create_product_variants(self, product, values):
        """Create product variants from attributes and values"""
        for attr_name in values['Variant Attributes'].split(','):
            attribute = self.env['product.attribute'].search(
                [('name', '=', attr_name.strip())], limit=1)
            if not attribute:
                raise UserError(_("Invalid attribute: %s") % attr_name)

            value_names = [v.strip() for v in
                           values['Attribute Values'].split(',')]
            value_ids = []
            for value_name in value_names:
                value = self.env['product.attribute.value'].search([
                    ('name', '=', value_name),
                    ('attribute_id', '=', attribute.id)
                ], limit=1)
                if not value:
                    raise UserError(
                        _("Invalid attribute value: %s for attribute: %s") % (
                        value_name, attr_name))
                value_ids.append(value.id)

            self.env['product.template.attribute.line'].create({
                'product_tmpl_id': product.id,
                'attribute_id': attribute.id,
                'value_ids': [(6, 0, value_ids)]
            })
