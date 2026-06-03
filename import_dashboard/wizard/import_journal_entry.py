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
from odoo import Command, fields, models


class ImportJournalEntry(models.TransientModel):
    """ Model for import Journal entry """
    _name = 'import.journal.entry'
    _description = 'Journal Entry Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xlsx', 'XLSX File')],
        string='Import File Type', default='csv',
        help="It helps to choose the file type")
    file = fields.Binary(string="File", help="File name")
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
        string="Import entry by", help="Product import")
    type = fields.Selection(
        selection=[('out_invoice', 'Invoice'), ('in_invoice', 'Bill'),
                   ('out_refund', 'Credit Note'), ('in_refund', 'Refund')],
        string='Invoicing Type', required=True, help="Entry type",
        default="out_invoice")

    def get_val(self, item, *keys, default=None):
        for key in keys:
            if item.get(key):
                return item.get(key)
        return default

    def set_journal_entry_lines(self, item, warning_msg, error_msg,
                          import_error_msg, row_not_import_msg, row):
        """Setting up the entry lines for the Journal entries"""
        account_account = self.env['account.account']
        uom_uom = self.env['uom.uom']
        account_tax = self.env['account.tax']
        product_model = self.env['product.product']
        line_vals = {}
        pro_vals = {}
        to_continue = False
        # --- LABEL ---
        label = self.get_val(item, 'Label', 'Entry Lines/Label', 'Entry lines/Label')
        if label:
            line_vals['name'] = label
        else:
            product_name = self.get_val(item, 'Product', 'Entry Lines/Product', 'Entry lines/Product')
            if not product_name:
                import_error_msg += row_not_import_msg + (
                    "\n\t⚠ Product and Label missing in file!"
                )
                to_continue = True
        # --- ACCOUNT ---
        account_code = self.get_val(item, 'Account Code', 'Entry Lines/Account Code', 'Entry lines/Account Code')
        if account_code:
            account = account_account.search(
                [('code', '=', int(account_code))], limit=1
            )
            line_vals['account_id'] = account.id
        # --- QUANTITY ---
        line_vals['quantity'] = self.get_val(
            item, 'Quantity', 'Entry Lines/Quantity', 'Entry lines/Quantity', default=1.0
        )
        # --- UOM ---
        uom_name = self.get_val(item, 'Uom', 'Entry Lines/Uom', 'Entry lines/Uom')
        if uom_name:
            uom = uom_uom.search([('name', '=', uom_name)], limit=1)
            if uom:
                line_vals['product_uom_id'] = uom.id
                pro_vals['uom_id'] = uom.id
        # --- PRICE ---
        price = self.get_val(item, 'Price', 'Entry Lines/Price', 'Entry lines/Price', 'Unit Price', 'Entry Lines/Price Unit', 'Entry lines/Price Unit')
        if price:
            line_vals['price_unit'] = price
            pro_vals['lst_price'] = price
        # --- DISCOUNT ---
        discount = self.get_val(
            item,
            'Disc.%', 'Entry Lines/Disc.%', 'Entry lines/Disc.%',
            'Disc', 'Entry Lines/Disc', 'Entry lines/Disc',
            'Discount', 'Entry Lines/Discount', 'Entry lines/Discount'
        )
        if discount:
            line_vals['discount'] = discount
        # --- TAX ---
        tax_name = self.get_val(item, 'Taxes', 'Entry Lines/Taxes', 'Entry lines/Taxes', 'Tax', 'Entry Lines/Tax', 'Entry lines/Tax')
        if tax_name:
            tax_amount = re.findall(r"(\d+)%", tax_name)
            tax = account_tax.search([
                ('name', '=', tax_name),
                ('type_tax_use', '=', 'sale')
            ], limit=1)
            if not tax:
                tax = account_tax.create({
                    'name': tax_name,
                    'type_tax_use': 'sale',
                    'amount': float(tax_amount[0]) if tax_amount else 0.0
                })
            line_vals['tax_ids'] = [tax.id]
            pro_vals['taxes_id'] = [tax.id]
        # --- PRODUCT ---
        product_name = self.get_val(item, 'Product', 'Entry Lines/Product', 'Entry lines/Product')
        internal_ref = self.get_val(item, 'Internal Reference', 'Entry Lines/Internal Reference', 'Entry lines/Internal Reference')
        barcode = self.get_val(item, 'Barcode', 'Entry Lines/Barcode', 'Entry lines/Barcode')
        product = False
        if self.import_product_by == 'name':
            if product_name:
                product = product_model.search(
                    [('name', '=', product_name)], limit=1
                )
                pro_vals['name'] = product_name
                if not product:
                    product = product_model.create(pro_vals)
            else:
                error_msg += row_not_import_msg + "\n\t⚠ Product name missing in file!"
                to_continue = True
        elif self.import_product_by == 'default_code':
            if internal_ref:
                product = product_model.search(
                    [('default_code', '=', internal_ref)], limit=1
                )
                if not product:
                    pro_vals['name'] = internal_ref
                    product = product_model.create(pro_vals)
                    warning_msg += f"\n◼ Product created from Internal Reference (row {row})"
            else:
                error_msg += row_not_import_msg + "\n\t⚠ Internal Reference missing!"
                to_continue = True
        elif self.import_product_by == 'barcode':
            if barcode:
                product = product_model.search(
                    [('barcode', '=', barcode)], limit=1
                )
                if not product:
                    pro_vals['name'] = barcode
                    product = product_model.create(pro_vals)
                    warning_msg += f"\n◼ Product created from Barcode (row {row})"
            else:
                error_msg += row_not_import_msg + "\n\t⚠ Barcode missing!"
                to_continue = True
        if product:
            line_vals['product_id'] = product.id
        return line_vals, error_msg, warning_msg, import_error_msg, to_continue

    def action_import_journal_entry(self):
        """Creating journal Entry record using uploaded xl/csv files"""
        account_move = self.env['account.move']
        res_partner = self.env['res.partner']
        res_users = self.env['res.users']
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
        imported_entries = []
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
                # --- PARTNER ---
                partner_name = self.get_val(item, 'Partner', 'Customer')
                if partner_name:
                    partner = res_partner.search(
                        [('name', '=', partner_name)])
                    if not partner:
                        partner = res_partner.create({
                            'name': partner_name
                        })
                        vals['partner_id'] = partner.id
                        if partner_added_msg:
                            partner_added_msg += (
                                "\n\t\trow {rn}: {partner}").format(
                                rn=row, partner=partner_name)
                        else:
                            partner_added_msg += (
                                    partner_msg + "\n\t\trow {rn}: "
                                                  "\"{partner}\"").format(
                                rn=row, partner=partner_name)
                    elif len(partner) > 1:
                        if import_error_msg:
                            import_error_msg += (
                                    "\n\t\t⚠ Multiple Partners with "
                                    "name (%s) found!"
                                    % partner_name)
                        else:
                            import_error_msg += row_not_import_msg + (
                                    "\n\t\t⚠ Multiple Partners with name (%s) found!"
                                    % partner_name)
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
                # --- PAYMENT REF ---
                payment_ref = self.get_val(item, 'Payment Reference')
                if payment_ref:
                    vals['payment_reference'] = payment_ref
                # --- Entry DATE ---
                invoice_date_val = self.get_val(item, 'Invoice Date', 'Bill Date')
                if invoice_date_val:
                    date = invoice_date_val
                    try:
                        invoice_date = datetime.datetime.strptime(date,
                                                                  '%m/%d/%Y')
                        vals['invoice_date'] = invoice_date
                    except:
                        if import_error_msg:
                            import_error_msg += ("\n\t\t⚠ Please check the date"
                                                 " format of Invoice/Bill Date is "
                                                 "mm/dd/yyyy")
                        else:
                            import_error_msg += row_not_import_msg + (
                                "\n\t\t⚠ Please check the date format of "
                                "Invoice/Bill Date is mm/dd/yyyy")
                # --- DUE DATE ---
                due_date_val = self.get_val(item, 'Due Date')
                if due_date_val:
                    date = due_date_val
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
                # --- SALESPERSON ---
                salesperson = self.get_val(item, 'Salesperson')
                if salesperson:
                    sales_person = res_users.search([('name', '=', salesperson)])
                    if sales_person:
                        vals['invoice_user_id'] = sales_person.id
                if import_error_msg:
                    error_msg += import_error_msg
                    continue
                # --- Entry SEARCH ---
                number = self.get_val(item, 'Number')
                invoice = account_move.search(
                    [('name', '=', number),
                     ('move_type', '=', vals['move_type'])])
                if invoice:
                    if len(invoice) > 1:
                        error_msg += row_not_import_msg + (
                                "\n\t⚠ Multiple invoices/bills with same Number(%s) "
                                "found!"
                                % number)
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
                        if number:
                            vals['name'] = number
                            invoice = account_move.create(vals)
                        else:
                            error_msg += (row_not_import_msg +
                                          fields_msg +
                                          "\n\t\t\"Number\"")
                            continue
                # --- LINES ---
                line_vals, error_msg, warning_msg, import_error_msg, to_continue = self.set_journal_entry_lines(
                    item,
                    warning_msg,
                    error_msg,
                    import_error_msg,
                    row_not_import_msg,
                    row
                )
                if to_continue:
                    continue
                if self.import_product_by and line_vals:
                    invoice.write({
                        'invoice_line_ids': [Command.create(line_vals)]
                    })
                imported += 1
                imported_entries += [invoice]
                if self.auto_post and imported_entries:
                    for inv in imported_entries:
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
        return False
