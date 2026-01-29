# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import base64
import datetime
import binascii
import csv
import io
import re
import tempfile
import xlrd
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ImportPurchaseOrder(models.TransientModel):
    """Model for importing purchase orders. This model facilitates the
    importing of purchase orders from CSV or XLSX files."""
    _name = 'import.purchase.order'
    _description = 'For importing purchase order'

    name = fields.Char(string="Name", help="Name",
                       default="Import Purchase Order")
    file_type = fields.Selection([('csv', 'CSV File'),
                                  ('xlsx', 'XLSX File')], default='csv',
                                 string='Select File Type',
                                 help="File type to import")
    file_upload = fields.Binary(string="File", help="Upload file")
    auto_confirm_quot = fields.Boolean(
        string='Confirm Quotation Automatically',
        help="Automatically confirm the quotation")
    order_number = fields.Selection(
        [('from_system', 'From System'),
         ('from_file', 'From File')], default='from_file',
        string='Reference', help="Order reference creation methods")
    import_product_by = fields.Selection(
        [('name', 'Name'), ('default_code', 'Internal Reference'),
         ('barcode', 'Barcode')], string="Import Product By", default='name',
        help="Import products by internal reference of barcode")

    def action_purchase_order_import(self):
        """Creating purchase record using uploaded xl/csv files"""
        items = {}
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(_(
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file and try again!"))
            items = csv_reader
        if self.file_type == 'xlsx':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False,
                                                 suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.seek(0)
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except:
                raise ValidationError(_(
                    "File not Valid.\n\nPlease check the type and format of "
                    "the file and try again!"))
            headers = sheet.row_values(0)  # list
            data = []
            for row_index in range(1, sheet.nrows):
                row = sheet.row_values(row_index)  # list
                data += [{k: v for k, v in zip(headers, row)}]
            items = data
        row = 0
        imported = 0
        error_msg = ""
        vendor_added_msg = ""
        date_missing_msg = ""
        warning_msg = ""
        previous_order = None
        for item in items:
            row += 1
            vals = {}
            row_not_import_msg = "\n❌Row {rn} not imported.".format(rn=row)
            import_error_msg = ""
            missing_fields_msg = ""
            vendor_msg = "\n🆕New Vendor(s) added:"
            if item.get('Vendor'):
                vendor = self.env['res.partner'].search(
                    [('name', '=', item['Vendor'])])
                if not vendor:
                    vendor = self.env['res.partner'].create({
                        'name': item['Vendor']})
                    vendor_added_msg += (
                            vendor_msg + "\n\t\trow {rn}: "
                                         "\"{vendor}\"").format(
                        rn=row, vendor=item['Vendor'])
                elif len(vendor) > 1:
                    import_error_msg += row_not_import_msg + (
                            "\n\t\t❎Multiple Partners with name (%s) found!"
                            % item['Vendor'])
                vals['partner_id'] = vendor.id
            if missing_fields_msg:
                import_error_msg += (row_not_import_msg +
                                     missing_fields_msg)
            if item.get('Vendor Reference'):
                vals['partner_ref'] = item['Vendor Reference']
            if item.get('Order Deadline'):
                date = item['Order Deadline']
                try:
                    order_deadline_date = datetime.datetime.strptime(
                        date, '%m/%d/%Y')
                    vals['date_order'] = order_deadline_date
                except:
                    import_error_msg += ("\n\t\t⚠ Please check the "
                                         "Order Deadline Date and format is "
                                         "mm/dd/yyyy")
            if item.get('Receipt Date'):
                receipt_date = item['Receipt Date']
                try:
                    receipt_date_date = datetime.datetime.strptime(
                        receipt_date, '%m/%d/%Y')
                    vals['date_planned'] = receipt_date_date
                except:
                    import_error_msg += ("\n\t\t⚠ Please check the "
                                         "Receipt Date and format is "
                                         "mm/dd/yyyy")
            if item.get('Purchase Representative'):
                vals['user_id'] = self.env['res.users'].search(
                    [('name', '=', item['Purchase Representative'])]).id
            if import_error_msg:
                error_msg += import_error_msg
                continue
            product = None
            line_vals = {}
            pro_vals = {}
            if item.get('Quantity'):
                line_vals['product_qty'] = item['Quantity']
            if item.get('Uom'):
                uom = self.env['uom.uom'].search(
                    [('name', '=', item['Uom'])])
                pro_vals['uom_id'] = line_vals['product_uom'] = uom.id
            if item.get('Unit Price'):
                pro_vals['lst_price'] = line_vals['price_unit'] = item[
                    'Unit Price']
            if item.get('Taxes'):
                tax_name = item['Taxes']
                tax_amount = (re.findall(r"(\d+)%", tax_name))[0]
                tax = self.env['account.tax'].search(
                    [('name', '=', tax_name),
                     ('type_tax_use', '=', 'purchase')], limit=1)
                if not tax:
                    tax = self.env['account.tax'].create({
                        'name': tax_name,
                        'type_tax_use': 'purchase',
                        'amount': tax_amount if tax_amount else 0.0
                    })
                pro_vals['taxes_id'] = line_vals['taxes_id'] = [tax.id]
            if self.import_product_by == 'name':
                if item.get('Product'):
                    product = self.env['product.product'].search(
                        [('name', '=',
                          item['Product'])])
                    if not product:
                        pro_vals['name'] = item['Product']
                        product = self.env['product.product'].create(
                            pro_vals)
                    if len(product) > 1:
                        if item.get('Variant Values'):
                            pro_tmpl_id = product.mapped('product_tmpl_id')
                            if len(pro_tmpl_id) > 1:
                                error_msg += row_not_import_msg + (
                                        "\n\t❎Multiple Product records are "
                                        "linked with the product variant \"%s\""
                                        "." % (item['Product']))
                                continue
                            variant_values = item['Variant Values'].split(
                                ',')
                            variant_value_ids = []
                            for var in variant_values:
                                k_v = var.partition(":")
                                attr = k_v[0].strip()
                                attr_val = k_v[2].strip()
                                var_attr_ids = self.env[
                                    'product.attribute'].search(
                                    [('name', '=', attr)]).ids
                                var_attr_val_ids = self.env[
                                    'product.attribute.value'].search(
                                    [('name', '=', attr_val),
                                     ('attribute_id', 'in',
                                      var_attr_ids)]).ids
                                pro_temp_attr_val_id = self.env[
                                    'product.template.attribute.value'].search(
                                    [('product_attribute_value_id', 'in',
                                      var_attr_val_ids),
                                     ('product_tmpl_id', '=',
                                      pro_tmpl_id.id)]).id
                                variant_value_ids += [pro_temp_attr_val_id]
                            if variant_value_ids:
                                product = product.filtered(
                                    lambda p:
                                    p.product_template_variant_value_ids.ids
                                    == variant_value_ids)
                            else:
                                error_msg += row_not_import_msg + (
                                        "\n\t❎Product variant with variant "
                                        "values \"%s\" not found."
                                        % (item['Variant Values']))
                                continue
                            if len(product) != 1:
                                error_msg += row_not_import_msg + (
                                        "\n\t❎Multiple variants with same "
                                        "Variant Values \"%s\" found. "
                                        "Please check if the product "
                                        "Variant Values are unique."
                                        % (item['Variant Values']))
                                continue
                        else:
                            error_msg += row_not_import_msg + (
                                    "\n\t⚠ Multiple Products with same "
                                    "Name \"%s\" found. Please "
                                    "provide unique product \"Variant "
                                    "Values\" to filter the records."
                                    % (item['Product']))
                            continue
                else:
                    error_msg += row_not_import_msg + (
                        "\n\t❎Product name missing in file!")
                    continue
            if self.import_product_by == 'default_code':
                if item.get('Internal Reference'):
                    product = self.env['product.product'].search(
                        [('default_code', '=',
                          item['Internal Reference'])])
                    if not product:
                        if not item.get('Product'):
                            warning_msg += ("\nℹA Product is created with "
                                            "\"Internal Reference\" as "
                                            "product name since \"Product\""
                                            " name is missing at row %d."
                                            % row)
                            pro_vals['name'] = item['Internal Reference']
                        product = self.env['product.product'].create(
                            pro_vals)
                    if len(product) > 1:
                        error_msg += row_not_import_msg + (
                                "\n\t❎Multiple Products with same Internal "
                                "Reference(%s) found!"
                                % (item['Internal Reference']))
                        continue
                else:
                    error_msg += row_not_import_msg + (
                        "\n\t❎Internal Reference missing in file!")
                    continue
            if self.import_product_by == 'barcode':
                if item.get('Barcode'):
                    product = self.env['product.product'].search(
                        [('barcode', '=',
                          item['Barcode'])])
                    if not product:
                        if not item.get('Product'):
                            warning_msg += (
                                    "\nℹNo value under \"Product\" at "
                                    "row %d, thus added \"Barcode\" as "
                                    "product name" % row)
                            pro_vals['name'] = item['Barcode']
                            product = self.env['product.product'].create(
                                pro_vals)
                    if len(product) > 1:
                        error_msg += row_not_import_msg + (
                                "\n\t❎Other Product(s) with same "
                                "Barcode (%s) found!" % item['Barcode'])
                        continue
                else:
                    error_msg += row_not_import_msg + (
                        "\n\t❎Barcode missing in file!")
                    continue
            line_vals['product_id'] = product.id
            vals['order_line'] = [(0, 0, line_vals)]
            purchase_order = self.env['purchase.order'].search(
                [('name', '=', item.get('Order Reference'))])
            if purchase_order:
                if len(purchase_order) > 1:
                    error_msg += row_not_import_msg + (
                            "\n\t❎Multiple purchase order with same Order "
                            "Reference(%s) found!"
                            % (item.get('Order Reference')))
                    continue
                if vals and purchase_order.state in ['draft', 'sent']:
                    purchase_order.write(vals)
                previous_order = purchase_order
            elif not purchase_order:
                if self.order_number == 'from_file':
                    vals['name'] = item.get('Order Reference')
                if item.get('Vendor'):
                    purchase_order = self.env['purchase.order'].create(vals)
                    if self.auto_confirm_quot:
                        purchase_order.button_confirm()
                    previous_order = purchase_order
            if item.get('Product') and not item.get('Vendor'):
                previous_order.write({
                    'order_line': [(0, 0, line_vals)]
                })
            imported += 1
        if error_msg:
            error_msg = "\n\n⚠ WARNING ⚠" + error_msg
        msg = (("Imported %d records."
                % imported) + vendor_added_msg +
               date_missing_msg + error_msg + warning_msg)
        message = self.env['import.message'].create(
            {'message': msg})
        if message:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Imported Successfully',
                    'type': 'rainbow_man',
                }
            }
