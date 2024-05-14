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
import binascii
import csv
import datetime
import io
import re
import tempfile
import xlrd
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ImportInvoice(models.TransientModel):
    """For handling importing of invoices"""
    _name = 'import.invoice'
    _description = 'For handling importing of invoices'

    name = fields.Char(string="Name", help="Name", default="Import Invoice")
    file_type = fields.Selection([('csv', 'CSV File'),
                                  ('xlsx', 'XLSX File')],
                                 string='Import File Type', default='csv',
                                 help="It helps to choose the file type")
    file = fields.Binary(string="File", help="Upload File")
    update_posted = fields.Boolean(string='Update Posted Record?',
                                   help='If enabled, the records in the '
                                        '"Posted" state will be converted to '
                                        'draft and their values will be '
                                        'updated. These records will be '
                                        'reposted if the "Post Automatically" '
                                        'is activated.')
    auto_post = fields.Boolean(string='Post Automatically',
                               help="Automatically post the invoice")
    journal = fields.Selection([('Bank', 'Bank'), ('Cash', 'Cash')],
                               string='Journal', default='Bank',
                               help='It helps to choose Journal type')
    order_number = fields.Selection(
        [('from_system', 'From System'),
         ('from_file', 'From File')],
        string='Number', default='from_file', help="Sequence number of orders")
    import_product_by = fields.Selection(
        [('name', 'Name'),
         ('default_code', 'Internal Reference'), ('barcode', 'Barcode')],
        string="Import Products BY", required=True,
        help="Importing of products by internal reference or barcode")
    type = fields.Selection(
        [('out_invoice', 'Invoice'), ('in_invoice', 'Bill'),
         ('out_refund', 'Credit Note'), ('in_refund', 'Refund')],
        string='Invoicing Type', required=True, help="Type of invoice")

    def action_invoice_import(self):
        """Creating Invoice record using uploaded xl/csv files"""
        items = {}
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file)
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
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except:
                raise ValidationError(_(
                    "File not Valid.\n\nPlease check the "
                    "type and format of the file and try again!"))
            headers = sheet.row_values(0)
            data = []
            for row_index in range(1, sheet.nrows):
                row = sheet.row_values(row_index)
                data += [{k: v for k, v in zip(headers, row)}]
            items = data
        row = 0
        imported = 0
        confirmed = 0
        imported_invoices = []
        error_msg = ""
        partner_added_msg = ""
        warning_msg = ""
        for item in items:
            row += 1
            vals = {}
            row_not_import_msg = "\n❌Row {rn} not imported.".format(rn=row)
            import_error_msg = ""
            missing_fields_msg = ""
            fields_msg = "\n\t🚫Missing required field(s):"
            partner_msg = "\n🆕New Partner(s) added:"
            vals['move_type'] = self.type
            if item.get('Partner'):
                partner = self.env['res.partner'].search(
                    [('name', '=', item['Partner'])])
                if not partner:
                    partner = self.env['res.partner'].create({
                        'name': item['Partner']
                    })
                    if partner_added_msg:
                        partner_added_msg += (
                            "\n\t\trow {rn}: {partner}").format(
                            rn=row, partner=item['Partner'])
                    else:
                        partner_added_msg += (
                                partner_msg + "\n\t\trow {rn}: "
                                              "\"{partner}\"").format(
                            rn=row, partner=item['Partner'])
                elif len(partner) > 1:
                    if import_error_msg:
                        import_error_msg += (
                                "\n\t\t⚠ Multiple Partners with "
                                "name (%s) found!"
                                % item['Partner'])
                    else:
                        import_error_msg += row_not_import_msg + (
                                "\n\t\t⚠ Multiple Partners with name (%s) found!"
                                % item['Partner'])
                vals['partner_id'] = partner.id
            else:
                if missing_fields_msg:
                    missing_fields_msg += "\n\t\t❗ \"Partner\""
                else:
                    missing_fields_msg += (fields_msg +
                                           "\n\t\t❗ \"Partner\"")
            if import_error_msg:
                import_error_msg += missing_fields_msg
            elif missing_fields_msg:
                import_error_msg += (row_not_import_msg +
                                     missing_fields_msg)
            if item.get('Payment Reference'):
                vals['payment_reference'] = item['Payment Reference']
            if item.get('Invoice Date'):
                date = item['Invoice Date']
                try:
                    inv_date = datetime.datetime.strptime(
                        date, '%m/%d/%Y')
                    vals['invoice_date'] = inv_date
                except:
                    import_error_msg += ("\n\t\t⚠ Please check the "
                                         "Quotation Date and format is "
                                         "mm/dd/yyyy")
            if item.get('Due Date'):
                vals['invoice_date_due'] = inv_date = datetime.datetime.strptime(
                    item.get('Due Date'), '%m/%d/%Y')
            if item.get('Salesperson'):
                vals['invoice_user_id'] = self.env['res.users'].search(
                    [('name', '=',
                      item['Salesperson'])]).id
            line_vals = {}
            pro_vals = {}
            if item.get('Label'):
                line_vals['name'] = item['Label']
            else:
                if not item.get('Product'):
                    import_error_msg += row_not_import_msg + (
                        "\n\t⚠ Product and Label missing in "
                        "file!")
                    continue
            if item.get('Account Code'):
                line_vals['account_id'] = self.env['account.account'].search(
                    [('code', '=', int(item['Account Code']))]).id
            if item.get('Quantity'):
                line_vals['quantity'] = item['Quantity']
            if item.get('Uom'):
                uom = self.env['uom.uom'].search([('name', '=', item['Uom'])])
                pro_vals['uom_id'] = line_vals['product_uom_id'] = uom.id
            if item.get('Price'):
                pro_vals['lst_price'] = line_vals['price_unit'] = item[
                    'Price']
            if item.get('Disc.%'):
                line_vals['discount'] = item['Disc.%']
            if item.get('Taxes'):
                tax_name = item['Taxes']
                tax_amount = (re.findall(r"(\d+)%", tax_name))[0]
                tax = self.env['account.tax'].search([('name', '=', tax_name),
                                                      ('type_tax_use', '=',
                                                       'sale')],
                                                     limit=1)
                if not tax:
                    tax = self.env['account.tax'].create({
                        'name': tax_name,
                        'type_tax_use': 'sale',
                        'amount': tax_amount if tax_amount else 0.0
                    })
                pro_vals['taxes_id'] = line_vals['tax_ids'] = [tax.id]
            product = None
            if self.import_product_by == 'name':
                if item.get('Product'):
                    product = self.env['product.product'].search(
                        [('name', '=', item['Product'])])
                    if not product:
                        pro_vals['name'] = item['Product']
                        pro_vals['default_code'] = item['Internal Reference']
                        product = self.env['product.product'].create(pro_vals)
                    if len(product) > 1:
                        if item.get('Variant Values'):
                            pro_tmpl_id = product.mapped('product_tmpl_id')
                            if len(pro_tmpl_id) > 1:
                                error_msg += row_not_import_msg + (
                                        "\n\t⚠ Multiple Product records are "
                                        "linked with the product variant \"%s\""
                                        "." % item['Product'])
                                continue
                            variant_values = item['Variant Values'].split(',')
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
                                    'product.attribute.value'].search(
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
                                        "\n\t⚠ Product variant with variant "
                                        "values \"%s\" not found."
                                        % (item['Variant Values']))
                                continue
                            if len(product) != 1:
                                error_msg += row_not_import_msg + (
                                        "\n\t⚠ Multiple variants with same "
                                        "Variant Values \"%s\" found. Please "
                                        "check if the product Variant Values"
                                        " are unique."
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
                        "\n\t⚠ Product name missing in file!")
                    continue
            if self.import_product_by == 'default_code':
                if item.get('Internal Reference'):
                    product = self.env['product.product'].search(
                        [('default_code', '=',
                          item['Internal Reference'])])
                    if not product:
                        if not item.get('Product'):
                            warning_msg += (
                                    "\n◼ A Product is created with "
                                    "\"Internal Reference\" as "
                                    "product name since \"Product\""
                                    " name is missing in file."
                                    "(row %d)" % row)
                            pro_vals['name'] = item['Internal Reference']
                        product = self.env['product.product'].create(pro_vals)
                    if len(product) > 1:
                        error_msg += row_not_import_msg + (
                                "\n\t⚠ Multiple Products with same Internal"
                                " Reference(%s) found!"
                                % item['Internal Reference'])
                        continue
                else:
                    error_msg += row_not_import_msg + (
                        "\n\t⚠ Internal Reference missing in file!")
                    continue
            # Product_by barcode
            if self.import_product_by == 'barcode':
                if item.get('Barcode'):
                    product = self.env['product.product'].search(
                        [('barcode', '=', item['Barcode'])])
                    if not product:
                        if not item.get('Product'):
                            warning_msg += (
                                    "\n◼ No value under \"Product\" at "
                                    "row %d, thus added \"Barcode\" as "
                                    "product name" % row)
                            pro_vals['name'] = item['Barcode']
                        product = self.env['product.product'].create(pro_vals)
                    if len(product) > 1:
                        error_msg += row_not_import_msg + (
                                "\n\t⚠ Other Product(s) with same "
                                "Barcode (%s) found!" % item['Barcode'])
                        continue
                else:
                    error_msg += row_not_import_msg + (
                        "\n\t⚠ Barcode missing in file!")
                    continue
            line_vals['product_id'] = product.id
            vals['invoice_line_ids'] = [(0, 0, line_vals)]
            vals['auto_post'] = self.auto_post
            invoice = self.env['account.move'].search(
                [('name', '=', item.get('Number')),
                 ('move_type', '=', vals['move_type'])])
            if invoice:
                if len(invoice) > 1:
                    error_msg += row_not_import_msg + (
                            "\n\t⚠ Multiple invoice with same Number(%s) "
                            "found!"
                            % item['Number'])
                    continue
                if vals:
                    if self.update_posted and invoice.state == 'posted':
                        invoice.button_draft()
                        invoice.write(vals)
                    elif invoice.state == 'draft':
                        invoice.write(vals)
            elif not invoice:
                if self.order_number == 'from_file':
                    vals['name'] = item['Number']
                if item.get('Partner'):
                    invoice = self.env['account.move'].create(vals)
            previous = invoice
            if item.get('Product') and not item.get('Partner'):
                previous.write({
                    'invoice_line_ids': [(0, 0, line_vals)]
                })
            imported += 1
            imported_invoices += [invoice]
            if self.auto_post and imported_invoices:
                confirmed = len(imported_invoices)
        if error_msg:
            error_msg = "\n\n🏮 WARNING 🏮" + error_msg
        msg = (("Imported %d records.\nConfirmed %d records"
                % (imported, confirmed)) + partner_added_msg + error_msg +
               warning_msg)
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
