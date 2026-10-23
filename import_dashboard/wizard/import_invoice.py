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
import datetime
import io
import re
from openpyxl import load_workbook
from openpyxl.utils.datetime import CALENDAR_MAC_1904, CALENDAR_WINDOWS_1900, from_excel

from .import_utils import get_file_content
from odoo.exceptions import ValidationError
from odoo import fields, models


class ImportInvoice(models.TransientModel):
    """ Model for import invoice """
    _name = 'import.invoice'
    _description = 'Invoice Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xlsx', 'XLSX File')],
        string='Import File Type', default='csv',
        help="Type of the file to import")
    file = fields.Binary(help="File to import")
    update_posted = fields.Boolean(
        string='Update Posted Record?',
        help='If enabled, the records in "Posted" state will converted to draft'
             ' and values are updated. These records will then again be posted'
             ' if "Post Automatically" is activated')
    auto_post = fields.Boolean(string='Post Automatically',
                               help="Post the invoices after import")
    order_number = fields.Selection(
        selection=[('from_system', 'From System'), ('from_file', 'From File')],
        string='Number', default='from_file', help="Take the invoice number from the file or from the system sequence")
    import_product_by = fields.Selection(
        selection=[('name', 'Name'), ('default_code', 'Internal Reference'),
                   ('barcode', 'Barcode')], required=True, default="name",
        string="Match Products By", help="Product field used to match the products in the file")
    type = fields.Selection(
        selection=[('out_invoice', 'Invoice'), ('in_invoice', 'Bill'),
                   ('out_refund', 'Credit Note'), ('in_refund', 'Refund')],
        string='Invoicing Type', required=True, help="Type of the invoices to import",
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

        # Support workbook datemode for xlsx -> default None for csv
        workbook_datemode = None

        # Helpers: header normalization + date parsing
        def _normalize_header(h):
            if h is None:
                return ''
            s = str(h).strip().strip('"\'').lower()
            s = re.sub(r'[\s_\-]+', ' ', s)
            return s

        HEADER_MAP = {
            'partner': 'Partner',
            'partner name': 'Partner',
            'customer': 'Partner',
            'customer name': 'Partner',
            'vendor': 'Partner',
            'vendor name': 'Partner',
            'client': 'Partner',
            'client name': 'Partner',
            'contact': 'Partner',
            'contact name': 'Partner',

            'product': 'Product',
            'product name': 'Product',
            'item': 'Product',

            'label': 'Label',
            'description': 'Label',

            'account code': 'Account Code',
            'account': 'Account Code',

            'price': 'Price',
            'unit price': 'Price',
            'cost': 'Price',
            'rate': 'Price',

            'quantity': 'Quantity',
            'qty': 'Quantity',

            'uom': 'Uom',
            'unit of measure': 'Uom',

            'taxes': 'Taxes',
            'tax': 'Taxes',

            'internal reference': 'Internal Reference',
            'default code': 'Internal Reference',
            'reference': 'Internal Reference',
            'ref': 'Internal Reference',

            'barcode': 'Barcode',

            'number': 'Number',
            'invoice number': 'Number',
            'bill number': 'Number',
            'invoice no': 'Number',
            'bill no': 'Number',

            'invoice date': 'Invoice Date',
            'inv date': 'Invoice Date',
            'bill date': 'Invoice Date',
            'date': 'Invoice Date',

            'due date': 'Due Date',

            'salesperson': 'Salesperson',
            'sales person': 'Salesperson',

            'payment reference': 'Payment Reference',
            'payment ref': 'Payment Reference',

            'variant values': 'Variant Values',

            'disc.%': 'Disc.%',
            'discount': 'Disc.%',
            'disc': 'Disc.%'
        }

        # Date parsing helper (handles strings, datetime objects, Excel serials)
        def _parse_date(value):
            """
            Return a datetime.date or raise ValueError.
            Accepts:
              - datetime.date / datetime.datetime
              - Excel serial numbers (float/int) if workbook_datemode available
              - Strings in several common formats
            """
            if value in (None, ''):
                return None
            # Already a date/datetime
            if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
                return value
            if isinstance(value, datetime.datetime):
                return value.date()
            # Excel numeric date (from xlsx): ctype gave us a float in sheet.row_values
            if isinstance(value, (float, int)):
                if workbook_datemode is not None:
                    try:
                        dt = from_excel(value, CALENDAR_MAC_1904 if workbook_datemode else CALENDAR_WINDOWS_1900)
                        return dt.date()
                    except Exception:
                        raise ValueError("Invalid Excel date serial: %s" % value)
                else:
                    # No workbook datemode — treat numeric as invalid
                    raise ValueError("Numeric date encountered but workbook datemode is unknown.")
            # Try string formats
            if isinstance(value, str):
                value = value.strip()
                # Some CSV exports may contain timestamps; remove time portion if present
                if ' ' in value and value.count(':') >= 1:
                    # keep only date part
                    value = value.split(' ')[0].strip()
                # formats to attempt (order matters)
                fmts = ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y', '%Y/%m/%d', '%m-%d-%Y']
                for f in fmts:
                    try:
                        dt = datetime.datetime.strptime(value, f)
                        return dt.date()
                    except Exception:
                        continue
            raise ValueError("Unrecognized date format: %s" % value)

        # Read file into normalized items list
        items = []
        raw_data = get_file_content(self, 'file')
        if self.file_type == 'csv':
            try:
                content = raw_data.decode("utf-8-sig", errors="replace").replace('\r\r\n', '\r\n')
                sample = content[:4096]
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
                    delimiter = dialect.delimiter
                except Exception:
                    delimiter = ','
                data_file = io.StringIO(content, newline='')
                reader = csv.DictReader(data_file, delimiter=delimiter)
                for raw in reader:
                    row = {}
                    for raw_key, raw_val in raw.items():
                        nk = _normalize_header(raw_key)
                        row_key = HEADER_MAP.get(nk, raw_key.strip() if raw_key else raw_key)
                        row[row_key] = raw_val
                    items.append(row)
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the type and format "
                               "of the file and try again!"))

        if self.file_type == 'xlsx':
            try:
                workbook = load_workbook(io.BytesIO(raw_data), data_only=True)
                sheet = workbook.active
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the "
                               "type and format of the file and try again!"))
            rows = list(sheet.iter_rows(values_only=True))
            raw_headers = list(rows[0]) if rows else []
            norm_headers = [_normalize_header(h) for h in raw_headers]
            headers = []
            for nh, rh in zip(norm_headers, raw_headers):
                headers.append(HEADER_MAP.get(
                    nh, rh.strip() if isinstance(rh, str) else rh))
            for row_vals in rows[1:]:
                if all(c is None or str(c).strip() == '' for c in row_vals):
                    continue
                items.append({k: v for k, v in zip(headers, row_vals)
                              if k is not None})

        # Carry-forward Number, Partner, Invoice Date for continuation rows
        last_number = None
        last_partner = None
        last_date = None
        for it in items:
            num = it.get('Number')
            if isinstance(num, str):
                num = num.strip() or None
            if num:
                last_number = num
            elif last_number:
                it['Number'] = last_number

            p = it.get('Partner') or it.get('Customer') or it.get('Vendor') or it.get('Client') or it.get('Contact')
            if isinstance(p, str):
                p = p.strip() or None
            if p:
                last_partner = p
                it['Partner'] = p
            elif last_partner:
                it['Partner'] = last_partner

            d = it.get('Invoice Date')
            if d:
                last_date = d
            elif last_date:
                it['Invoice Date'] = last_date

        # Main import loop
        row = 0
        imported = 0
        confirmed = 0
        imported_invoices = account_move
        error_msg = ""
        partner_added_msg = ""
        warning_msg = ""
        if items:
            for item in items:
                row += 1
                vals = {}
                row_not_import_msg = self.env._("\n❌Row %(rn)s not imported.", rn=row)
                import_error_msg = ""
                missing_fields_msg = ""
                fields_msg = self.env._("\n\tMissing required field(s):")
                partner_msg = self.env._("\n🆕New Partner(s) added:")
                vals['move_type'] = self.type

                # Partner
                partner_name = item.get('Partner') or item.get('Customer') or item.get('Vendor') or item.get('Client') or item.get('Contact')
                if isinstance(partner_name, str):
                    partner_name = partner_name.strip() or None
                if partner_name:
                    partner = res_partner.search([('name', '=', partner_name)])
                    if not partner:
                        partner = res_partner.create({'name': partner_name})
                        vals['partner_id'] = partner.id
                        if partner_added_msg:
                            partner_added_msg += self.env._("\n\t\trow %(rn)s: %(partner)s", rn=row, partner=partner_name)
                        else:
                            partner_added_msg += (partner_msg + "\n\t\trow {rn}: "
                                                                "\"{partner}\"").format(rn=row, partner=partner_name)
                    elif len(partner) > 1:
                        import_error_msg += row_not_import_msg + (
                                self.env._("\n\t\t⚠ Multiple Partners with name (%s) found!", partner_name))
                    else:
                        vals['partner_id'] = partner.id
                else:
                    if missing_fields_msg:
                        missing_fields_msg += self.env._("\n\t\t❗ \"Partner\"")
                    else:
                        missing_fields_msg += (fields_msg + self.env._("\n\t\t❗ \"Partner\""))

                # Missing fields accumulation
                if import_error_msg:
                    import_error_msg += missing_fields_msg
                elif missing_fields_msg:
                    import_error_msg += (row_not_import_msg + missing_fields_msg)

                # Payment reference
                if item.get('Payment Reference'):
                    vals['payment_reference'] = item['Payment Reference']

                # Invoice date
                if item.get('Invoice Date'):
                    date = item['Invoice Date']
                    try:
                        invoice_date = _parse_date(date)
                        if invoice_date:
                            vals['invoice_date'] = invoice_date
                    except ValueError as e:
                        import_error_msg += row_not_import_msg + (
                                self.env._("\n\t\t⚠ Please check the date format of Invoice Date. (%s)", e))

                # Due date
                if item.get('Due Date'):
                    date = item['Due Date']
                    try:
                        due_date = _parse_date(date)
                        if due_date:
                            vals['invoice_date_due'] = due_date
                    except ValueError as e:
                        import_error_msg += row_not_import_msg + (
                                self.env._("\n\t\t⚠ Please check the date format of Due Date. (%s)", e))

                # Salesperson
                if item.get('Salesperson'):
                    sales_person = res_users.search([('name', '=', item['Salesperson'])], limit=1)
                    if sales_person:
                        vals['invoice_user_id'] = sales_person.id

                # If any import-level error so far, skip this row
                if import_error_msg:
                    error_msg += import_error_msg
                    continue

                # Find or create invoice
                invoice = account_move.search(
                    [('name', '=', item.get('Number')), ('move_type', '=', vals['move_type'])])
                if invoice:
                    if len(invoice) > 1:
                        error_msg += row_not_import_msg + (
                                self.env._("\n\t⚠ Multiple invoices with the same number (%s) found!", item.get('Number')))
                        continue
                    if vals:
                        if self.update_posted and invoice.state == 'posted':
                            invoice.button_draft()
                            invoice.write(vals)
                        elif invoice.state == 'draft':
                            invoice.write(vals)
                else:
                    if self.order_number == 'from_system':
                        invoice = account_move.create(vals)
                    elif self.order_number == 'from_file':
                        if item.get('Number'):
                            vals['name'] = item['Number']
                            invoice = account_move.create(vals)
                        else:
                            error_msg += (row_not_import_msg + fields_msg + self.env._("\n\t\t\"Number\""))
                            continue

                # Prepare invoice line values
                line_vals = {}
                pro_vals = {}

                # Description fallback: Label > Product > Internal Reference > Barcode
                label_value = item.get('Label') or False
                product_value = item.get('Product') or item.get('Internal Reference') or item.get('Barcode') or False

                if label_value:
                    line_vals['name'] = label_value
                elif product_value:
                    line_vals['name'] = product_value
                else:
                    has_amount_info = bool(item.get('Price')) or bool(item.get('Quantity'))
                    if has_amount_info:
                        line_vals['name'] = "Imported Line (row %d)" % row
                        warning_msg += self.env._("\n◼ Row %d: no Product/Label — created generic line description.", row)
                    else:
                        import_error_msg += row_not_import_msg + self.env._("\n\t⚠ Product and Label missing in file!")
                        error_msg += import_error_msg
                        continue

                # Safe account lookup
                if item.get('Account Code'):
                    raw_code = str(item['Account Code']).strip()
                    account = account_account.search([('code', '=', raw_code)], limit=1)
                    if not account:
                        try:
                            num = int(float(raw_code))
                            account = account_account.search([('code', '=', str(num))], limit=1)
                        except Exception:
                            account = False
                    if account:
                        line_vals['account_id'] = account.id

                # Quantity
                if item.get('Quantity'):
                    # try numeric conversion
                    try:
                        line_vals['quantity'] = float(item.get('Quantity'))
                    except Exception:
                        line_vals['quantity'] = item.get('Quantity')

                # UoM
                if item.get('Uom'):
                    uom = uom_uom.search([('name', '=', item['Uom'])], limit=1)
                    if uom:
                        pro_vals['uom_id'] = line_vals['product_uom_id'] = uom.id

                # Price
                if item.get('Price'):
                    try:
                        price_val = float(item.get('Price'))
                        pro_vals['lst_price'] = line_vals['price_unit'] = price_val
                    except Exception:
                        pro_vals['lst_price'] = line_vals['price_unit'] = item.get('Price')

                # Discount
                if item.get('Disc.%'):
                    try:
                        line_vals['discount'] = float(item.get('Disc.%'))
                    except Exception:
                        line_vals['discount'] = item.get('Disc.%')

                # Taxes
                if item.get('Taxes'):
                    tax_name = item['Taxes']
                    m = re.findall(r"(\d+)%", tax_name)
                    tax_amount = m[0] if m else 0.0
                    tax_type = 'purchase' if self.type in ['in_invoice', 'in_refund'] else 'sale'
                    tax = account_tax.search([('name', '=', tax_name), ('type_tax_use', '=', tax_type)], limit=1)
                    if not tax:
                        tax = account_tax.create({
                            'name': tax_name,
                            'type_tax_use': tax_type,
                            'amount': float(tax_amount) if tax_amount else 0.0
                        })
                    if tax_type == 'purchase':
                        pro_vals['supplier_taxes_id'] = [tax.id]
                    else:
                        pro_vals['taxes_id'] = [tax.id]
                    line_vals['tax_ids'] = [tax.id]

                # Product fields
                if item.get('Product'):
                    pro_vals['name'] = item['Product']
                if item.get('Internal Reference'):
                    pro_vals['default_code'] = item['Internal Reference']
                if item.get('Barcode'):
                    pro_vals['barcode'] = item['Barcode']

                # Product resolution depending on import_product_by
                product = False
                if self.import_product_by == 'name':
                    if item.get('Product'):
                        product = product_product.search([('name', '=', item['Product'])])
                        if not product:
                            # create product with provided pro_vals
                            product = product_product.create(pro_vals)
                        if len(product) > 1:
                            # handle variants if provided
                            if item.get('Variant Values'):
                                pro_tmpl_id = product.mapped('product_tmpl_id')
                                if len(pro_tmpl_id) > 1:
                                    error_msg += row_not_import_msg + (
                                            self.env._("\n\t⚠ Multiple Product records are linked with the product variant \"%s\".", item['Product']))
                                    continue
                                variant_values = item['Variant Values'].split(',')
                                variant_value_ids = []
                                for var in variant_values:
                                    k_v = var.partition(":")
                                    attr = k_v[0].strip()
                                    attr_val = k_v[2].strip()
                                    var_attr_ids = product_attribute.search([('name', '=', attr)]).ids
                                    var_attr_val_ids = product_attribute_value.search(
                                        [('name', '=', attr_val), ('attribute_id', 'in', var_attr_ids)]).ids
                                    if var_attr_val_ids:
                                        pro_temp_attr_val_id = product_template_attribute_value.search(
                                            [('product_attribute_value_id', 'in', var_attr_val_ids),
                                             ('product_tmpl_id', '=', pro_tmpl_id.id)]).id
                                        variant_value_ids += [pro_temp_attr_val_id]
                                if variant_value_ids:
                                    product = product.filtered(
                                        lambda p: p.product_template_variant_value_ids.ids == variant_value_ids)
                                else:
                                    error_msg += row_not_import_msg + (
                                            self.env._("\n\t⚠ No product variant with the Variant Values \"%s\" was found.", item['Variant Values']))
                                    continue
                                if len(product) != 1:
                                    error_msg += row_not_import_msg + (
                                            self.env._("\n\t⚠ Multiple variants with the same Variant Values \"%s\" found.", item['Variant Values']))
                                    continue
                            else:
                                error_msg += row_not_import_msg + (
                                        self.env._("\n\t⚠ Multiple products with the same name \"%s\" found. Please provide unique variant values.", item['Product']))
                                continue
                    else:
                        error_msg += row_not_import_msg + (self.env._("\n\tProduct name missing in file!"))
                        continue

                if self.import_product_by == 'default_code':
                    if item.get('Internal Reference'):
                        product = product_product.search([('default_code', '=', item['Internal Reference'])])
                        if not product:
                            if not item.get('Product'):
                                warning_msg += (
                                            self.env._("\n◼ A product was created with the \"Internal Reference\" as its name because the \"Product\" name is missing in the file. (row %d)", row))
                                pro_vals['name'] = item['Internal Reference']
                            product = product_product.create(pro_vals)
                        if len(product) > 1:
                            error_msg += row_not_import_msg + (
                                    self.env._("\n\t⚠ Multiple products with the same Internal Reference (%s) found!", item[
                                'Internal Reference']))
                            continue
                    else:
                        error_msg += row_not_import_msg + (self.env._("\n\tInternal Reference missing in file!"))
                        continue

                if self.import_product_by == 'barcode':
                    if item.get('Barcode'):
                        product = product_product.search([('barcode', '=', item['Barcode'])])
                        if not product:
                            if not item.get('Product'):
                                warning_msg += (
                                            self.env._("\n◼ No value under \"Product\" at row %d, thus added \"Barcode\" as product name", row))
                                pro_vals['name'] = item['Barcode']
                            product = product_product.create(pro_vals)
                        if len(product) > 1:
                            error_msg += row_not_import_msg + (
                                        self.env._("\n\tOther products with the same Barcode (%s) found!", item['Barcode']))
                            continue
                    else:
                        error_msg += row_not_import_msg + (self.env._("\n\tBarcode missing in file!"))
                        continue

                # Attach product and create line
                if product:
                    line_vals['product_id'] = product.id

                # Add the line to the invoice
                invoice.write({'invoice_line_ids': [(0, 0, line_vals)]})

                imported += 1
                imported_invoices |= invoice

            # Post once all lines are added, skipping invoices already posted
            if self.auto_post:
                to_post = imported_invoices.filtered(lambda move: move.state == 'draft')
                to_post.action_post()
                confirmed = len(to_post)

            # Report errors if any
            if error_msg:
                error_msg = self.env._("\n\nWARNING") + error_msg
                error_message = self.env['import.message'].create({'message': error_msg})
                return {
                    'name': self.env._('Error!'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'import.message',
                    'res_id': error_message.id,
                    'target': 'new'
                }

            # Success message
            msg = ((self.env._("Imported %(imported)d records.\nPosted %(confirmed)d records", imported=imported, confirmed=confirmed)) + partner_added_msg + warning_msg)
            message = self.env['import.message'].create({'message': msg})
            if message:
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': msg,
                        'type': 'rainbow_man',
                    }
                }
