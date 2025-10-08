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
from odoo.exceptions import ValidationError
from odoo import fields, models


class ImportInvoice(models.TransientModel):
    """ Model for import invoice """
    _name = 'import.invoice'
    _description = 'Invoice Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xlsx', 'XLSX File')],
        string='Import File Type', default='csv',
        help="It helps to choose the file type")
    file = fields.Binary(string="File", help="File")
    update_posted = fields.Boolean(
        string='Update Posted Record?',
        help='If enabled, the records in "Posted" state will converted to draft'
             ' and values are updated. These records will then again be posted'
             ' if "Post Automatically" is activated')
    auto_post = fields.Boolean(string='Post Automatically',
                               help="Post Automatically")
    journal = fields.Selection(
        selection=[('Bank', 'Bank'), ('Cash', 'Cash')], string='Journal',
        default='Bank', help='It helps to choose Journal type')
    order_number = fields.Selection(
        selection=[('from_system', 'From System'), ('from_file', 'From File')],
        string='Number', default='from_file', help="Order number")
    import_product_by = fields.Selection(
        selection=[('name', 'Name'), ('default_code', 'Internal Reference'),
                   ('barcode', 'Barcode')], required=True, default="name",
        string="Import invoice by", help="Product import")
    type = fields.Selection(
        selection=[('out_invoice', 'Invoice'), ('in_invoice', 'Bill'),
                   ('out_refund', 'Credit Note'), ('in_refund', 'Refund')],
        string='Invoicing Type', required=True, help="Invoice type",
        default="out_invoice")

    def action_import_invoice(self):
        """Creating Invoice record using uploaded xl/csv files"""
        account_move = self.env['account.move']
        res_partner = self.env['res.partner']
        res_users = self.env['res.users']
        account_account = self.env['account.account']
        uom_uom = self.env['uom.uom']
        account_tax = self.env['account.tax']
        product_product = self.env['product.product']
        product_attribute = self.env['product.attribute']
        product_attribute_value = self.env['product.attribute.value']
        product_template_attribute_value = self.env[
            'product.template.attribute.value']
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file and try again!")
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
                raise ValidationError(
                    "File not Valid.\n\nPlease check the "
                    "type and format of the file and try again!")
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
        if items:
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
                    partner = res_partner.search(
                        [('name', '=', item['Partner'])])
                    if not partner:
                        partner = res_partner.create({
                            'name': item['Partner']
                        })
                        vals['partner_id'] = partner.id
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
                    else:
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
                        invoice_date = datetime.datetime.strptime(date,
                                                                  '%m/%d/%Y')
                        vals['invoice_date'] = invoice_date
                    except:
                        if import_error_msg:
                            import_error_msg += ("\n\t\t⚠ Please check the date"
                                                 " format of Invoice Date is "
                                                 "mm/dd/yyyy")
                        else:
                            import_error_msg += row_not_import_msg + (
                                "\n\t\t⚠ Please check the date format of "
                                "Invoice Date is mm/dd/yyyy")
                if item.get('Due Date'):
                    date = item['Due Date']
                    try:
                        due_date = datetime.datetime.strptime(date, '%m/%d/%Y')
                        vals['invoice_date_due'] = due_date
                    except:
                        if import_error_msg:
                            import_error_msg += ("\n\t\t⚠ Please check the date"
                                                 " format of Due Date is "
                                                 "mm/dd/yyyy")
                        else:
                            import_error_msg += row_not_import_msg + (
                                "\n\t\t⚠ Please check the date format of Due "
                                "Date is mm/dd/yyyy")
                if item.get('Salesperson'):
                    sales_person = res_users.search([('name', '=',
                                                      item['Salesperson'])])
                    if sales_person:
                        vals['invoice_user_id'] = sales_person.id
                if import_error_msg:
                    error_msg += import_error_msg
                    continue
                invoice = account_move.search(
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
                    if self.order_number == 'from_system':
                        invoice = account_move.create(vals)
                    if self.order_number == 'from_file':
                        if item.get('Number'):
                            vals['name'] = item['Number']
                            invoice = account_move.create(vals)
                        else:
                            error_msg += (row_not_import_msg +
                                          fields_msg +
                                          "\n\t\t\"Number\"")
                            continue
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
                    account = account_account.search(
                        [('code', '=', int(item['Account Code']))])
                    line_vals['account_id'] = account.id
                if item.get('Quantity'):
                    line_vals['quantity'] = item['Quantity']
                if item.get('Uom'):
                    uom = uom_uom.search([('name', '=', item['Uom'])])
                    if uom:
                        pro_vals['uom_id'] = line_vals[
                            'product_uom_id'] = uom.id
                if item.get('Price'):
                    pro_vals['lst_price'] = line_vals['price_unit'] = item[
                        'Price']
                if item.get('Disc.%'):
                    line_vals['discount'] = item['Disc.%']
                if item.get('Taxes'):
                    tax_name = item['Taxes']
                    tax_amount = (re.findall(r"(\d+)%", tax_name))[0]
                    tax = account_tax.search([('name', '=', tax_name),
                                              ('type_tax_use', '=', 'sale')],
                                             limit=1)
                    if not tax:
                        tax = account_tax.create({
                            'name': tax_name,
                            'type_tax_use': 'sale',
                            'amount': tax_amount if tax_amount else 0.0
                        })
                    pro_vals['taxes_id'] = line_vals['tax_ids'] = [tax.id]
                if item.get('Product'):
                    pro_vals['name'] = item['Product']
                if item.get('Internal Reference'):
                    pro_vals['default_code'] = item['Internal Reference']
                if self.import_product_by == 'name':
                    if item.get('Product'):
                        product = product_product.search(
                            [('name', '=', item['Product'])])
                        if not product:
                            product = product_product.create(pro_vals)
                        if len(product) > 1:
                            if item.get('Variant Values'):
                                pro_tmpl_id = product.mapped('product_tmpl_id')
                                if len(pro_tmpl_id) > 1:
                                    error_msg += row_not_import_msg + (
                                            "\n\t⚠ Multiple Product records are"
                                            "linked with the product variant "
                                            "\"%s\""
                                            "." % item['Product'])
                                    continue
                                variant_values = item['Variant Values'].split(
                                    ',')
                                variant_value_ids = []
                                for var in variant_values:
                                    k_v = var.partition(":")
                                    attr = k_v[0].strip()
                                    attr_val = k_v[2].strip()
                                    var_attr_ids = product_attribute.search(
                                        [('name', '=', attr)]).ids
                                    var_attr_val_ids = (product_attribute_value.
                                                        search(
                                        [('name', '=', attr_val),
                                         ('attribute_id', 'in',
                                          var_attr_ids)]).ids)
                                    pro_temp_attr_val_id = (
                                        product_template_attribute_value.search(
                                            [(
                                             'product_attribute_value_id', 'in',
                                             var_attr_val_ids),
                                             ('product_tmpl_id', '=',
                                              pro_tmpl_id.id)]).id)
                                    variant_value_ids += [pro_temp_attr_val_id]
                                if variant_value_ids:
                                    product = product.filtered(
                                        lambda p:
                                        p.product_template_variant_value_ids.ids
                                        == variant_value_ids)
                                else:
                                    error_msg += row_not_import_msg + (
                                            "\n\t⚠ Product variant with variant"
                                            "values \"%s\" not found."
                                            % (item['Variant Values']))
                                    continue
                                if len(product) != 1:
                                    error_msg += row_not_import_msg + (
                                            "\n\t⚠ Multiple variants with same "
                                            "Variant Values \"%s\" found. "
                                            "Please"
                                            "check if the product Variant "
                                            "Values"
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
                        product = product_product.search(
                            [('default_code', '=', item['Internal Reference'])])
                        if not product:
                            if not item.get('Product'):
                                warning_msg += ("\n◼ A Product is created with "
                                                "\"Internal Reference\" as "
                                                "product name since \"Product\""
                                                " name is missing in file."
                                                "(row %d)" % row)
                                pro_vals['name'] = item['Internal Reference']
                            product = product_product.create(pro_vals)
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
                        product = product_product.search(
                            [('barcode', '=', item['Barcode'])])
                        if not product:
                            if not item.get('Product'):
                                warning_msg += (
                                        "\n◼ No value under \"Product\" at "
                                        "row %d, thus added \"Barcode\" as "
                                        "product name" % row)
                                pro_vals['name'] = item['Barcode']
                            product = product_product.create(pro_vals)
                        if len(product) > 1:
                            error_msg += row_not_import_msg + (
                                    "\n\t⚠ Other Product(s) with same "
                                    "Barcode (%s) found!" % item['Barcode'])
                            continue
                    else:
                        error_msg += row_not_import_msg + (
                            "\n\t⚠ Barcode missing in file!")
                        continue
                if self.import_product_by and product:
                    line_vals['product_id'] = product.id
                    invoice.write({
                        'invoice_line_ids': [(0, 0, line_vals)]
                    })
                imported += 1
                imported_invoices += [invoice]
                if self.auto_post and imported_invoices:
                    for inv in imported_invoices:
                        inv.action_post()
                        confirmed += 1
            if error_msg:
                error_msg = "\n\n🏮 WARNING 🏮" + error_msg
                error_message = self.env['import.message'].create(
                    {'message': error_msg})
                return {
                    'name': 'Error!',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'import.message',
                    'res_id': error_message.id,
                    'target': 'new'
                }
            msg = (("Imported %d records.\nPosted %d records"
                    % (imported, confirmed)) + partner_added_msg +
                   warning_msg)
            message = self.env['import.message'].create(
                {'message': msg})
            if message:
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': msg,
                        'type': 'rainbow_man',
                    }
                }
