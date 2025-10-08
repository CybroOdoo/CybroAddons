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


class ImportSaleOrder(models.TransientModel):
    """ Model for import sale orders. """
    _name = 'import.sale.order'
    _description = 'Sale Order Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xlsx', 'XLSX File')],
        string='Select File Type', default='csv', help='File type')
    file_upload = fields.Binary(string="Upload File",
                                help="Helps to upload your file")
    auto_confirm_quot = fields.Boolean(
        string='Confirm Quotation Automatically',
        help='Automatically confirm the quotation')
    order_number = fields.Selection(
        selection=[('from_system', 'From System'),
                   ('from_file', 'From File')],
        string='Order / Quotation Number', default='from_file',
        help='Order or Quotation Number')
    import_product_by = fields.Selection(
        selection=[('name', 'Name'),
                   ('default_code', 'Internal Reference'),
                   ('barcode', 'Barcode')], default='name',
        string="Import order by", help="import product")

    def action_import_sale_order(self):
        """Creating sale order record using uploaded xl/csv files"""
        sale_order = self.env['sale.order']
        res_partner = self.env['res.partner']
        res_users = self.env['res.users']
        product_product = self.env['product.product']
        product_attribute = self.env['product.attribute']
        product_attribute_value = self.env['product.attribute.value']
        product_template_attribute_value = self.env[
            'product.template.attribute.value']
        account_tax = self.env['account.tax']
        uom_uom = self.env['uom.uom']
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format of "
                    "the file and try again!")
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
                raise ValidationError(
                    "File not Valid.\n\nPlease check the "
                    "type and format of the file and try again!")
            headers = sheet.row_values(0)
            data = []
            for row_index in range(1, sheet.nrows):
                row = sheet.row_values(row_index)  # list
                data += [{k: v for k, v in zip(headers, row)}]
            items = data
        row = 0
        imported = 0
        confirmed = 0
        imported_saleorders = []
        error_msg = ""
        cust_added_msg = ""
        warning_msg = ""
        if items:
            for item in items:
                row += 1
                vals = {}
                row_not_import_msg = "\n◼  Row {rn} not imported.".format(
                    rn=row)
                import_error_msg = ""
                missing_fields_msg = ""
                fields_msg = "\n\t\t🚫Missing required field(s):"
                cust_msg = "\n🆕New Customer(s) added:"
                if not item.get('Order Reference'):
                    if missing_fields_msg:
                        missing_fields_msg += "\n\t\t\t❗ \"Order Reference\" "
                    else:
                        missing_fields_msg += (fields_msg +
                                               "\n\t\t\t❗ \"Order Reference\"")
                if item.get('Customer'):
                    customer = res_partner.search(
                        [('name', '=', item['Customer'])])
                    if not customer:
                        customer = res_partner.create({
                            'name': item['Customer']
                        })
                        vals['partner_id'] = customer.id
                        if cust_added_msg:
                            cust_added_msg += (
                                "\n\t\trow {rn}: {cust}").format(
                                rn=row, cust=item['Customer'])
                        else:
                            cust_added_msg += (
                                    cust_msg + "\n\t\trow {rn}: "
                                               "\"{cust}\"").format(
                                rn=row, cust=item['Customer'])
                    elif len(customer) > 1:
                        if import_error_msg:
                            import_error_msg += (
                                    "\n\t\t⚠ Multiple Partners with"
                                    " name (%s) found!"
                                    % item['Customer'])
                        else:
                            import_error_msg += row_not_import_msg + (
                                    "\n\t\t⚠ Multiple Partners with name (%s) "
                                    "found!"
                                    % item['Customer'])
                    else:
                        vals['partner_id'] = customer.id
                else:
                    if missing_fields_msg:
                        missing_fields_msg += "\n\t\t\t❗ \"Customer\""
                    else:
                        missing_fields_msg += (fields_msg +
                                               "\n\t\t\t❗ \"Customer\"")
                if import_error_msg:
                    import_error_msg += missing_fields_msg
                elif missing_fields_msg:
                    import_error_msg += (row_not_import_msg +
                                         missing_fields_msg)
                if item.get('Quotation Date'):
                    date = item['Quotation Date']
                    try:
                        quot_date = datetime.datetime.strptime(
                            date, '%m/%d/%Y')
                        vals['date_order'] = quot_date
                    except:
                        if import_error_msg:
                            import_error_msg += ("\n\t\t⚠ Please check the "
                                                 "Quotation Date and format is "
                                                 "mm/dd/yyyy")
                        else:
                            import_error_msg += row_not_import_msg + (
                                "\n\t\t⚠ Please check the Quotation Date and "
                                "format is mm/dd/yyyy")

                if item.get('Salesperson'):
                    sales_person = res_users.search(
                        [('name', '=', item['Salesperson'])])
                    if sales_person:
                        vals['user_id'] = sales_person.id
                if import_error_msg:
                    error_msg += import_error_msg
                    continue
                saleorder = sale_order.search(
                    [('name', '=', item['Order Reference'])])
                if saleorder:
                    if len(saleorder) > 1:
                        error_msg += row_not_import_msg + (
                                "\n\t⚠ Multiple sale order with same Order "
                                "Reference(%s) found!"
                                % (item['Order Reference']))
                        continue
                    if vals and saleorder.state in ['draft', 'sent']:
                        saleorder.write(vals)
                elif not saleorder:
                    if self.order_number == 'from_system':
                        saleorder = sale_order.create(vals)
                    if self.order_number == 'from_file':
                        vals['name'] = item.get('Order Reference')
                        saleorder = sale_order.create(vals)
                line_vals = {}
                pro_vals = {}
                if item.get('Description'):
                    line_vals['name'] = item['Description']
                if item.get('Quantity'):
                    line_vals['product_uom_qty'] = item['Quantity']
                if item.get('Uom'):
                    uom = uom_uom.search([('name', '=', item['Uom'])])
                    if uom:
                        pro_vals['uom_id'] = line_vals['product_uom'] = uom.id
                if item.get('Unit Price'):
                    pro_vals['lst_price'] = line_vals['price_unit'] = item[
                        'Unit Price']
                if item.get('Taxes'):
                    tax_name = item['Taxes']
                    tax_amount = (re.findall(r"(\d+)%", tax_name))[0]
                    tax = account_tax.search(
                        [('name', '=', tax_name),
                         ('type_tax_use', '=', 'sale')], limit=1)
                    if not tax:
                        tax = account_tax.create({
                            'name': tax_name,
                            'type_tax_use': 'sale',
                            'amount': tax_amount if tax_amount else 0.0
                        })
                    pro_vals['taxes_id'] = line_vals['tax_id'] = [tax.id]
                if item.get('Disc.%'):
                    line_vals['discount'] = item['Disc.%']
                if item.get('Product'):
                    pro_vals['name'] = item['Product']
                if item.get('Internal Reference'):
                    pro_vals['default_code'] = item['Internal Reference']
                if self.import_product_by == 'name':
                    if item.get('Product'):
                        product = product_product.search([('name', '=',
                                                           item['Product'])])
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
                                    % (item['Internal Reference']))
                            continue
                    else:
                        error_msg += row_not_import_msg + (
                            "\n\t⚠ Internal Reference missing in file!")
                        continue
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
                    saleorder.write({
                        'order_line': [(0, 0, line_vals)]
                    })
                imported += 1
                imported_saleorders += [saleorder]
            if self.auto_confirm_quot and imported_saleorders:
                for so in imported_saleorders:
                    so.action_confirm()
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
            msg = (("Imported %d records.\nConfirmed %d records"
                    % (imported, confirmed)) + cust_added_msg + warning_msg)
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
