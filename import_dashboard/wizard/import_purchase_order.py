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


class ImportPurchaseOrder(models.TransientModel):
    """ Model for import purchase orders. """
    _name = 'import.purchase.order'
    _description = 'Purchase Order import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xlsx', 'XLSX File')],
        string='Select File Type', default='csv',
        help="File type to import")
    file_upload = fields.Binary(string="File Upload",
                                help="Helps to upload your file")
    auto_confirm_quot = fields.Boolean(
        string='Confirm Quotation Automatically',
        help="Automatically confirm the quotation")
    order_number = fields.Selection(
        selection=[('from_system', 'From System'),
                   ('from_file', 'From File')],
        string='Reference', default='from_file', help="reference")
    import_product_by = fields.Selection(
        selection=[('name', 'Name'), ('default_code', 'Internal Reference'),
                   ('barcode', 'Barcode')],
        default="name", string="Import order by", help="import product")

    def get_val(self, item, *keys, default=None):
        for key in keys:
            if item.get(key):
                return item.get(key)
        return default

    def set_order_lines(self, item, import_error_msg, row_not_import_msg, error_msg, warning_msg, row):
        product_product = product = self.env['product.product']
        product_attribute = self.env['product.attribute']
        product_attribute_value = self.env['product.attribute.value']
        product_template_attribute_value = self.env[
            'product.template.attribute.value']
        account_tax = self.env['account.tax']
        uom_uom = self.env['uom.uom']
        to_continue = False
        line_vals = {}
        pro_vals = {}
        desc = self.get_val(item, 'Description', 'Order Lines/Description')
        if desc:
            line_vals['name'] = desc
        date = self.get_val(item, 'Delivery Date', 'Order Lines/Delivery Date')
        if date:
            try:
                line_vals['date_planned'] = datetime.datetime.strptime(date, '%m/%d/%Y')
            except:
                if import_error_msg:
                    import_error_msg += "\n\t\t❎Please check the Delivery Date and format is mm/dd/yyyy"
                else:
                    import_error_msg += row_not_import_msg + (
                        "\n\t\t❎Please check the Delivery Date and format is mm/dd/yyyy")
        qty = self.get_val(item, 'Quantity', 'Order Lines/Quantity')
        if qty:
            line_vals['product_qty'] = qty
        uom_name = self.get_val(item, 'Uom', 'Order Lines/Uom')
        if uom_name:
            uom = uom_uom.search([('name', '=', uom_name)])
            if uom:
                pro_vals['uom_id'] = line_vals['product_uom'] = uom.id
        price = self.get_val(item, 'Unit Price', 'Price', 'Order Lines/Unit Price', 'Order Lines/Price')
        if price:
            pro_vals['lst_price'] = line_vals['price_unit'] = price
        tax_name = self.get_val(item, 'Taxes', 'Order Lines/Taxes')
        if tax_name:
            tax_amount = (re.findall(r"(\d+)%", tax_name))[0]
            tax = account_tax.search(
                [('name', '=', tax_name),
                 ('type_tax_use', '=', 'purchase')], limit=1)
            if not tax:
                tax = account_tax.create({
                    'name': tax_name,
                    'type_tax_use': 'purchase',
                    'amount': tax_amount if tax_amount else 0.0
                })
            pro_vals['taxes_id'] = line_vals['taxes_id'] = [tax.id]
        product_name = self.get_val(item, 'Product', 'Order Lines/Product')
        if product_name:
            pro_vals['name'] = product_name
        internal_ref = self.get_val(item, 'Internal Reference', 'Order Lines/Internal Reference')
        if internal_ref:
            pro_vals['default_code'] = internal_ref
        barcode = self.get_val(item, 'Barcode', 'Order Lines/Barcode')
        # --- product selection logic ---
        if self.import_product_by == 'name':
            if product_name:
                product = product_product.search([('name', '=', product_name)])
                if not product:
                    product = product_product.create(pro_vals)
                if len(product) > 1:
                    variant_values_str = self.get_val(item, 'Variant Values', 'Order Lines/Variant Values')
                    if variant_values_str:
                        pro_tmpl_id = product.mapped('product_tmpl_id')
                        if len(pro_tmpl_id) > 1:
                            error_msg += row_not_import_msg + (
                                    "\n\t❎Multiple Product records are "
                                    "linked with the product variant "
                                    "\"%s\"." % product_name)
                            to_continue = True
                        variant_values = variant_values_str.split(',')
                        variant_value_ids = []
                        for var in variant_values:
                            k_v = var.partition(":")
                            attr = k_v[0].strip()
                            attr_val = k_v[2].strip()
                            var_attr_ids = product_attribute.search(
                                [('name', '=', attr)]).ids
                            var_attr_val_ids = product_attribute_value.search(
                                [('name', '=', attr_val),
                                 ('attribute_id', 'in', var_attr_ids)]).ids
                            pro_temp_attr_val_id = (
                                product_template_attribute_value.search(
                                    [('product_attribute_value_id', 'in', var_attr_val_ids),
                                     ('product_tmpl_id', '=', pro_tmpl_id.id)]).id)
                            variant_value_ids += [pro_temp_attr_val_id]
                        if variant_value_ids:
                            product = product.filtered(
                                lambda p: p.product_template_variant_value_ids.ids == variant_value_ids)
                        else:
                            error_msg += row_not_import_msg + (
                                    "\n\t❎Product variant with variant "
                                    "values \"%s\" not found."
                                    % variant_values_str)
                            to_continue = True
                        if len(product) != 1:
                            error_msg += row_not_import_msg + (
                                    "\n\t❎Multiple variants with same "
                                    "Variant Values \"%s\" found."
                                    % variant_values_str)
                            to_continue = True
                    else:
                        error_msg += row_not_import_msg + (
                                "\n\t⚠ Multiple Products with same Name \"%s\" found."
                                % product_name)
                        to_continue = True
            else:
                error_msg += row_not_import_msg + (
                    "\n\t❎Product name missing in file!")
                to_continue = True
        elif self.import_product_by == 'default_code':
            if internal_ref:
                product = product_product.search([('default_code', '=', internal_ref)])
                if not product:
                    if not product_name:
                        warning_msg += ("\nℹA Product is created with "
                                        "\"Internal Reference\" as product name"
                                        " at row %d." % row)
                        pro_vals['name'] = internal_ref
                    product = product_product.create(pro_vals)
                if len(product) > 1:
                    error_msg += row_not_import_msg + (
                            "\n\t❎Multiple Products with same Internal Reference(%s) found!"
                            % internal_ref)
                    to_continue = True
            else:
                error_msg += row_not_import_msg + (
                    "\n\t❎Internal Reference missing in file!")
                to_continue = True
        elif self.import_product_by == 'barcode':
            if barcode:
                product = product_product.search([('barcode', '=', barcode)])
                if not product:
                    if not product_name:
                        warning_msg += ("\nℹNo value under \"Product\" at row %d"
                                        % row)
                        pro_vals['name'] = barcode
                        product = product_product.create(pro_vals)
                if len(product) > 1:
                    error_msg += row_not_import_msg + (
                            "\n\t❎Other Product(s) with same Barcode (%s) found!"
                            % barcode)
                    to_continue = True
            else:
                error_msg += row_not_import_msg + (
                    "\n\t❎Barcode missing in file!")
                to_continue = True
        return line_vals, product, to_continue

    def action_import_purchase_order(self):
        """Creating purchase record using uploaded xl/csv files"""
        purchase_order = self.env['purchase.order']
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
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file and try again!")
            items = csv_reader
        if self.file_type == 'xlsx':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.seek(0)
                workbook = openpyxl.load_workbook(fp.name, data_only=True)
                sheet = workbook.active
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format of "
                    "the file and try again!")
            rows = list(sheet.rows)
            headers = [cell.value for cell in rows[0]]
            data = []
            for row in rows[1:]:
                data += [{k: v.value for k, v in zip(headers, row)}]
            items = data
        row = 0
        imported = 0
        confirmed = 0
        imported_purchaseorders = []
        error_msg = ""
        vendor_added_msg = ""
        warning_msg = ""
        if items:
            for item in items:
                row += 1
                vals = {}
                row_not_import_msg = "\n❌Row {rn} not imported.".format(rn=row)
                import_error_msg = ""
                missing_fields_msg = ""
                fields_msg = "\n\t🚫Missing required field(s):"
                vendor_msg = "\n🆕New Vendor(s) added:"
                order_ref = self.get_val(item, 'Order Reference')
                if not order_ref:
                    if missing_fields_msg:
                        missing_fields_msg += "\n\t\t\t\"❗Order Reference\" "
                    else:
                        missing_fields_msg += (fields_msg +
                                               "\n\t\t\t\"❗Order Reference\"")
                vendor_name = self.get_val(item, 'Vendor', 'Partner')
                if vendor_name:
                    vendor = res_partner.search([('name', '=', vendor_name)])
                    if not vendor:
                        vendor = res_partner.create({'name': vendor_name})
                        vals['partner_id'] = vendor.id
                        if vendor_added_msg:
                            vendor_added_msg += (
                                "\n\t\trow {rn}: {vendor}").format(
                                rn=row, vendor=vendor_name)
                        else:
                            vendor_added_msg += (
                                    vendor_msg + "\n\t\trow {rn}: "
                                                 "\"{vendor}\"").format(
                                rn=row, vendor=vendor_name)
                    elif len(vendor) > 1:
                        if import_error_msg:
                            import_error_msg += ("\n\t\t❎Multiple Partners with"
                                                 " name (%s) found!"
                                                 % vendor_name)
                        else:
                            import_error_msg += row_not_import_msg + (
                                    "\n\t\t❎Multiple Partners with name (%s) "
                                    "found!"
                                    % vendor_name)
                    else:
                        vals['partner_id'] = vendor.id
                else:
                    if missing_fields_msg:
                        missing_fields_msg += "\n\t\t\t\"❗Vendor\""
                    else:
                        missing_fields_msg += (fields_msg +
                                               "\n\t\t\t\"❗Vendor\"")
                if import_error_msg:
                    import_error_msg += missing_fields_msg
                elif missing_fields_msg:
                    import_error_msg += (row_not_import_msg +
                                         missing_fields_msg)
                vendor_ref = self.get_val(item, 'Vendor Reference')
                if vendor_ref:
                    vals['partner_ref'] = vendor_ref
                date = self.get_val(item, 'Order Deadline')
                if date:
                    try:
                        vals['date_order'] = datetime.datetime.strptime(date, '%m/%d/%Y')
                    except:
                        if import_error_msg:
                            import_error_msg += "\n\t\t❎Please check the Order Deadline and format is mm/dd/yyyy"
                        else:
                            import_error_msg += row_not_import_msg + (
                                "\n\t\t❎Please check the Order Deadline and format is mm/dd/yyyy")
                date = self.get_val(item, 'Receipt Date')
                if date:
                    try:
                        vals['date_planned'] = datetime.datetime.strptime(date, '%m/%d/%Y')
                    except:
                        if import_error_msg:
                            import_error_msg += "\n\t\t❎Please check the Receipt Date and format is mm/dd/yyyy"
                        else:
                            import_error_msg += row_not_import_msg + (
                                "\n\t\t❎Please check the Receipt Date and format is mm/dd/yyyy")
                purchase_rep = self.get_val(item, 'Purchase Representative', 'Representative')
                if purchase_rep:
                    user = res_users.search([('name', '=', purchase_rep)])
                    if user:
                        vals['user_id'] = user.id
                if import_error_msg:
                    error_msg += import_error_msg
                    continue
                purchaseorder = purchase_order.search([('name', '=', order_ref)])
                if purchaseorder:
                    if len(purchaseorder) > 1:
                        error_msg += row_not_import_msg + (
                                "\n\t❎Multiple purchase order with same Order "
                                "Reference(%s) found!"
                                % order_ref)
                        continue
                    if vals and purchaseorder.state in ['draft', 'sent']:
                        purchaseorder.write(vals)
                else:
                    if self.order_number == 'from_system':
                        purchaseorder = purchase_order.create(vals)
                    else:
                        vals['name'] = order_ref
                        purchaseorder = purchase_order.create(vals)
                line_vals, product, to_continue = self.set_order_lines(item, import_error_msg, row_not_import_msg,
                                                                       error_msg, warning_msg, row)
                if to_continue:
                    continue
                if self.import_product_by and product:
                    line_vals['product_id'] = product.id
                    purchaseorder.write({
                        'order_line': [Command.create(line_vals)]
                    })
                imported += 1
                imported_purchaseorders += [purchaseorder]
            if self.auto_confirm_quot and imported_purchaseorders:
                for po in imported_purchaseorders:
                    po.button_confirm()
                confirmed += 1
            if error_msg:
                error_msg = "\n\n⚠ WARNING ⚠" + error_msg
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
                    % (imported, confirmed)) + vendor_added_msg + warning_msg)
            message = self.env['import.message'].create({'message': msg})
            if message:
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': msg,
                        'type': 'rainbow_man',
                    }
                }
        return False
