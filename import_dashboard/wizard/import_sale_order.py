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
import openpyxl
from odoo.exceptions import ValidationError
from odoo import fields, models, Command


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
        help='Order/Quotation Number for newly creating Sale Order/Quotation')
    import_product_by = fields.Selection(
        selection=[('name', 'Name'),
                   ('default_code', 'Internal Reference'),
                   ('barcode', 'Barcode')], default='name',
        string="Import order by", help="import product")

    def get_val(self, item, *keys, default=None):
        for key in keys:
            if item.get(key):
                return item.get(key)
        return default

    def set_order_line_vals(self, item, row, error_msg, row_not_import_msg, warning_msg):
        """Setting up the Orderline values to be added to each order line"""
        to_continue = False
        barcode = ''
        product_product = self.env['product.product']
        product_attribute = self.env['product.attribute']
        product_attribute_value = self.env['product.attribute.value']
        product_template_attribute_value = self.env['product.template.attribute.value']
        account_tax = self.env['account.tax']
        uom_uom = self.env['uom.uom']
        line_vals = {}
        pro_vals = {}
        # -----------------------
        # Basic Fields
        # -----------------------
        description = self.get_val(item, 'Description', 'Order Lines/Description')
        quantity = self.get_val(item, 'Quantity', 'Order Lines/Quantity')
        uom_name = self.get_val(item, 'Uom', 'Order Lines/Uom')
        price = self.get_val(item, 'Unit Price', 'Order Lines/Unit Price')
        tax_name = self.get_val(item, 'Taxes', 'Order Lines/Taxes')
        discount = self.get_val(item,
                                'Disc.%', 'Order Lines/Disc.%',
                                'Disc', 'Order Lines/Disc',
                                'Discount', 'Order Lines/Discount'
                                )
        product_name = self.get_val(item, 'Product', 'Order Lines/Product')
        internal_ref = self.get_val(item, 'Internal Reference', 'Order Lines/Internal Reference')
        barcode_val = self.get_val(item, 'Barcode', 'Order Lines/Barcode')
        if description:
            line_vals['name'] = description
        if quantity:
            line_vals['product_uom_qty'] = quantity
        # -----------------------
        # UOM
        # -----------------------
        if uom_name:
            uom = uom_uom.search([('name', '=', uom_name)], limit=1)
            if uom:
                line_vals['product_uom'] = uom.id
                pro_vals['uom_id'] = uom.id
        # -----------------------
        # Price
        # -----------------------
        if price:
            line_vals['price_unit'] = price
            pro_vals['lst_price'] = price
        # -----------------------
        # Tax
        # -----------------------
        if tax_name:
            tax_amount = 0.0
            match = re.findall(r"(\d+)%", tax_name)
            if match:
                tax_amount = float(match[0])
            tax = account_tax.search([
                ('name', '=', tax_name),
                ('type_tax_use', '=', 'sale')
            ], limit=1)
            if not tax:
                tax = account_tax.create({
                    'name': tax_name,
                    'type_tax_use': 'sale',
                    'amount': tax_amount
                })
            line_vals['tax_id'] = [(6, 0, [tax.id])]
            pro_vals['taxes_id'] = [(6, 0, [tax.id])]
        # -----------------------
        # Discount
        # -----------------------
        if discount:
            line_vals['discount'] = discount
        # -----------------------
        # Product Base Values
        # -----------------------
        if product_name:
            pro_vals['name'] = product_name
        if internal_ref:
            pro_vals['default_code'] = internal_ref
        # -----------------------
        # Product Fetching Logic
        # -----------------------
        product = product_product
        if self.import_product_by == 'name':
            if not product_name:
                error_msg += row_not_import_msg + "\n\t⚠ Product name missing in file!"
                to_continue = True
            else:
                product = product_product.search([('name', '=', product_name)])
                if not product:
                    product = product_product.create(pro_vals)
                if len(product) > 1:
                    variant_values = item.get('Variant Values')
                    if variant_values:
                        pro_tmpl_ids = product.mapped('product_tmpl_id')
                        if len(pro_tmpl_ids) > 1:
                            error_msg += row_not_import_msg + (
                                f"\n\t⚠ Multiple Product templates found for \"{product_name}\"."
                            )
                            to_continue = True
                        variant_value_ids = []
                        for var in variant_values.split(','):
                            attr, _, val = var.partition(":")
                            attr = attr.strip()
                            val = val.strip()
                            attr_ids = product_attribute.search([('name', '=', attr)]).ids
                            val_ids = product_attribute_value.search([
                                ('name', '=', val),
                                ('attribute_id', 'in', attr_ids)
                            ]).ids
                            ptav = product_template_attribute_value.search([
                                ('product_attribute_value_id', 'in', val_ids),
                                ('product_tmpl_id', '=', pro_tmpl_ids.id)
                            ], limit=1)
                            if ptav:
                                variant_value_ids.append(ptav.id)
                        if variant_value_ids:
                            product = product.filtered(
                                lambda p: p.product_template_variant_value_ids.ids == variant_value_ids
                            )
                        else:
                            error_msg += row_not_import_msg + (
                                f"\n\t⚠ Variant values \"{variant_values}\" not found."
                            )
                            to_continue = True
                        if len(product) != 1:
                            error_msg += row_not_import_msg + (
                                f"\n\t⚠ Multiple variants found for \"{variant_values}\"."
                            )
                            to_continue = True
                    else:
                        error_msg += row_not_import_msg + (
                            f"\n\t⚠ Multiple products found with name \"{product_name}\"."
                        )
                        to_continue = True
        elif self.import_product_by == 'default_code':
            if not internal_ref:
                error_msg += row_not_import_msg + "\n\t⚠ Internal Reference missing in file!"
                to_continue = True
            else:
                product = product_product.search([('default_code', '=', internal_ref)])
                if not product:
                    if not product_name:
                        warning_msg += (
                            f"\n◼ Product created using Internal Reference at row {row}"
                        )
                        pro_vals['name'] = internal_ref

                    product = product_product.create(pro_vals)

                if len(product) > 1:
                    error_msg += row_not_import_msg + (
                        f"\n\t⚠ Multiple products found with Internal Reference ({internal_ref})"
                    )
                    to_continue = True
        elif self.import_product_by == 'barcode':
            if not barcode_val:
                error_msg += row_not_import_msg + "\n\t⚠ Barcode missing in file!"
                to_continue = True
            else:
                product = product_product.search([('barcode', '=', barcode_val)])
                if not product:
                    if not product_name:
                        warning_msg += (
                            f"\n◼ Product created using Barcode at row {row}"
                        )
                        pro_vals['name'] = barcode_val

                    product = product_product.create(pro_vals)
                if len(product) > 1:
                    error_msg += row_not_import_msg + (
                        f"\n\t⚠ Multiple products found with Barcode ({barcode_val})"
                    )
                    barcode = barcode_val
                    to_continue = True
        return error_msg, row_not_import_msg, to_continue, barcode, line_vals, product

    def action_import_sale_order(self):
        """Creating sale order record using uploaded xl/csv files"""
        sale_order = self.env['sale.order']
        res_partner = self.env['res.partner']
        res_users = self.env['res.users']
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
                workbook = openpyxl.load_workbook(fp.name, data_only=True)
                sheet = workbook.active
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the "
                    "type and format of the file and try again!")
            rows = list(sheet.rows)
            headers = [cell.value for cell in rows[0]]
            data = []
            for row in rows[1:]:
                data += [{k: v.value for k, v in zip(headers, row)}]
            items = data
        row = 0
        imported = 0
        confirmed = 0
        imported_sale_orders = []
        error_msg = ""
        cust_added_msg = ""
        warning_msg = ""
        if items:
            for item in items:
                row += 1
                vals = {}
                row_not_import_msg = "\n◼  Row {rn} not imported.".format(rn=row)
                import_error_msg = ""
                missing_fields_msg = ""
                fields_msg = "\n\t\t🚫Missing required field(s):"
                cust_msg = "\n🆕New Customer(s) added:"
                if not self.get_val(item, 'Order Reference', 'Reference', 'Order'):
                    if missing_fields_msg:
                        missing_fields_msg += "\n\t\t\t❗ \"Order Reference\" "
                    else:
                        missing_fields_msg += (fields_msg +
                                               "\n\t\t\t❗ \"Order Reference\"")
                customer_name = self.get_val(item, 'Customer', 'Partner')
                if customer_name:
                    customer = res_partner.search(
                        [('name', '=', customer_name)])
                    if not customer:
                        customer = res_partner.create({
                            'name': customer_name
                        })
                        vals['partner_id'] = customer.id
                        if cust_added_msg:
                            cust_added_msg += (
                                "\n\t\trow {rn}: {cust}").format(
                                rn=row, cust=customer_name)
                        else:
                            cust_added_msg += (
                                    cust_msg + "\n\t\trow {rn}: "
                                               "\"{cust}\"").format(
                                rn=row, cust=customer_name)
                    elif len(customer) > 1:
                        if import_error_msg:
                            import_error_msg += (
                                    "\n\t\t⚠ Multiple Partners with"
                                    " name (%s) found!"
                                    % customer_name)
                        else:
                            import_error_msg += row_not_import_msg + (
                                    "\n\t\t⚠ Multiple Partners with name (%s) "
                                    "found!"
                                    % customer_name)
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
                if self.get_val(item, 'Quotation Date', 'Date'):
                    date = self.get_val(item, 'Quotation Date', 'Date')
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
                if self.get_val(item, 'Salesperson'):
                    sales_person = res_users.search(
                        [('name', '=', self.get_val(item, 'Salesperson'))])
                    if sales_person:
                        vals['user_id'] = sales_person.id
                if import_error_msg:
                    error_msg += import_error_msg
                    continue
                order_ref = self.get_val(item, 'Order Reference', 'Reference')
                sale_order = sale_order.search(
                    [('name', '=', order_ref)])

                if sale_order:
                    if len(sale_order) > 1:
                        error_msg += row_not_import_msg + (
                                "\n\t⚠ Multiple sale order with same Order "
                                "Reference(%s) found!"
                                % order_ref)
                        continue
                    if vals and sale_order.state in ['draft', 'sent']:
                        sale_order.write(vals)
                elif not sale_order:
                    if self.order_number == 'from_system':
                        sale_order = sale_order.create(vals)
                    if self.order_number == 'from_file':
                        vals['name'] = order_ref
                        sale_order = sale_order.create(vals)
                error_msg, row_not_import_msg, to_continue, barcode, line_vals, product = self.set_order_line_vals(
                    item, row, error_msg, row_not_import_msg, warning_msg)
                if to_continue:
                    continue
                if self.import_product_by and product:
                    line_vals['product_id'] = product.id
                    sale_order.write({
                        'order_line': [Command.create(line_vals)]
                    })
                imported += 1
                imported_sale_orders += [sale_order]
            if self.auto_confirm_quot and imported_sale_orders:
                for so in imported_sale_orders:
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
        return False
