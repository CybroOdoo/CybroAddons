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
import os
import re
import tempfile
import openpyxl
from odoo.exceptions import ValidationError
from odoo import fields, models


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
        selection=[('name', 'Name'), ('default_code', 'Order Reference'),
                   ('barcode', 'Barcode')],
        default="name", string="Import order by", help="import product")

    # Add this helper inside class ImportPurchaseOrder (above action_import_purchase_order)
    DATE_PATTERNS = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y",
        "%Y.%m.%d", "%d.%m.%Y", "%m.%d.%Y",
        "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
        "%Y/%m/%d", "%Y %m %d"
    ]

    def _parse_date_value(self, value):
        """
        Robust date parser:
        - accepts datetime.date / datetime.datetime
        - accepts Excel serial numbers (int/float) using Excel epoch (1899-12-30)
        - accepts ISO formats
        - tries user's language date_format if available
        - falls back to DATE_PATTERNS
        Returns a naive datetime.datetime on success, or False on failure.
        """
        if value is None:
            return False

        # Already a datetime / date object
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            # convert date -> datetime (00:00:00)
            return datetime.datetime.combine(value, datetime.time())

        # Excel serial number (common when reading XLSX)
        if isinstance(value, (int, float)):
            try:
                # Excel's day 0 is 1899-12-30 in many exporters (covers most cases).
                base = datetime.datetime(1899, 12, 30)
                return base + datetime.timedelta(days=float(value))
            except Exception:
                pass

        s = str(value).strip()
        if not s:
            return False

        # Try ISO first (fast)
        try:
            # datetime.fromisoformat handles 'YYYY-MM-DD' and 'YYYY-MM-DDTHH:MM:SS'
            return datetime.datetime.fromisoformat(s)
        except Exception:
            pass

        # Try user language date format (if present)
        try:
            # Attempt to fetch the user's language format (best-effort)
            user_lang_code = getattr(self.env.user, 'lang', None)
            if user_lang_code:
                lang = self.env['res.lang'].search([('code', '=', user_lang_code)], limit=1)
                lang_fmt = getattr(lang, 'date_format', None)
                if lang_fmt:
                    try:
                        # res.lang.date_format typically uses Python strftime tokens already
                        return datetime.datetime.strptime(s, lang_fmt)
                    except Exception:
                        # Some lang formats include %-d etc. If that fails, fall back
                        pass
        except Exception:
            # Do not abort on lang lookup errors, fall back to patterns
            pass

        # Try list of common patterns
        for fmt in self.DATE_PATTERNS:
            try:
                return datetime.datetime.strptime(s, fmt)
            except Exception:
                continue

        # Last resort: try parsing with common separators in swapped day/month order
        # e.g., try switching day/month if format looks ambiguous like '01/02/2025'
        try:
            parts = re.split(r"[-/\. ]", s)
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                # try dd/mm/yyyy
                for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%Y-%m-%d"):
                    try:
                        return datetime.datetime.strptime(s, fmt)
                    except Exception:
                        pass
        except Exception:
            pass

        # Could not parse
        return False

    def action_import_purchase_order(self):
        """Creating purchase record using uploaded xl/csv files"""
        purchase_order = self.env['purchase.order']
        res_partner = self.env['res.partner']
        res_users = self.env['res.users']
        product_product = self.env['product.product']
        account_tax = self.env['account.tax']
        uom_uom = self.env['uom.uom']

        # Read file into items (list of dicts)
        items = []
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload or b'')
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
                items = list(csv_reader)
            except Exception:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file and try again!")
        elif self.file_type == 'xlsx':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload or b''))
                fp.flush()
                fp.close()
                workbook = openpyxl.load_workbook(fp.name, data_only=True)
                sheet = workbook.active
            except Exception:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format of "
                    "the file and try again!")
            rows = list(sheet.iter_rows(values_only=True))
            headers = list(rows[0]) if rows else []
            data = []
            for row in rows[1:]:
                if all(c is None or str(c).strip() == '' for c in row):
                    continue
                data.append({k: v for k, v in zip(headers, row) if k is not None})
            items = data
            try:
                os.unlink(fp.name)
            except Exception:
                pass

        # Defensive: ensure items is a list
        if not items:
            items = []

        # -------------------- Normalization --------------------
        # Normalize headers and values: map "Order Lines" -> "Product",
        # handle "Order Lines/Quantity" combined cells, trim whitespace, normalize empty-like values.
        normalized_items = []

        def _extract_product_and_qty_from_string(s):
            """Return tuple (product_name, qty_or_None)."""
            if s is None:
                return (None, None)
            s = str(s).strip()
            if not s:
                return (None, None)
            # Try delimiters where last token is numeric qty
            parts = re.split(r'\s*[\/|\-]\s*', s)
            if len(parts) >= 2 and re.fullmatch(r'\d+(\.\d+)?', parts[-1].strip()):
                qty = parts[-1].strip()
                prod = '/'.join(parts[:-1]).strip()
                return (prod, qty)
            # Try patterns like "Name (10)" or "Name x10"
            m = re.search(r'^(?P<prod>.*?)[\s\(\[]*[xX]?\s*(?P<qty>\d+(\.\d+)?)\s*[\)\]]*$', s)
            if m:
                prod = m.group('prod').strip()
                qty = m.group('qty').strip()
                if prod == '':
                    return (None, qty)
                return (prod, qty)
            # reversed "10 / Name"
            parts_rev = re.split(r'\s*[\/|\-]\s*', s)
            if len(parts_rev) >= 2 and re.fullmatch(r'\d+(\.\d+)?', parts_rev[0].strip()):
                qty = parts_rev[0].strip()
                prod = '/'.join(parts_rev[1:]).strip()
                return (prod, qty)
            return (s, None)

        for raw_item in items:
            if not isinstance(raw_item, dict):
                normalized_items.append(raw_item)
                continue
            norm = {}
            filled_product = False
            filled_quantity = False

            # iterate original columns
            for k, v in raw_item.items():
                if k is None:
                    continue
                header = k.strip() if isinstance(k, str) else k
                header_l = header.lower() if isinstance(header, str) else ''

                # Handle combined 'Order Lines' headers
                if isinstance(header, str) and header_l.startswith('order lines'):
                    # normalize v
                    value = v if not (isinstance(v, str) and v.strip().lower() in ('nan', 'none', '')) else None

                    # if numeric and explicit Product column exists elsewhere, treat as Quantity
                    if isinstance(value, (int, float)) and any(
                            isinstance(h, str) and h.strip().lower() == 'product' for h in raw_item.keys()):
                        if not filled_quantity:
                            norm['Quantity'] = value
                            filled_quantity = True
                        continue

                    if isinstance(value, str):
                        prod, qty = _extract_product_and_qty_from_string(value)
                        if prod:
                            norm['Product'] = prod
                            filled_product = True
                        if qty is not None:
                            try:
                                norm['Quantity'] = int(qty) if '.' not in qty else float(qty)
                            except Exception:
                                norm['Quantity'] = qty
                            filled_quantity = True
                        if not filled_product and value:
                            norm['Product'] = value
                            filled_product = True
                    else:
                        if isinstance(value, (int, float)):
                            if not filled_quantity:
                                norm['Quantity'] = value
                                filled_quantity = True
                        else:
                            norm[header] = value
                    continue

                # explicit Product header
                if isinstance(header, str) and header_l == 'product':
                    if isinstance(v, str):
                        vv = v.strip()
                        norm['Product'] = None if vv.lower() in ('', 'nan', 'none') else vv
                    else:
                        norm['Product'] = v
                    filled_product = True
                    continue

                # explicit Quantity header
                if isinstance(header, str) and header_l in ('quantity', 'qty'):
                    if isinstance(v, str):
                        vv = v.strip()
                        if vv == '':
                            norm['Quantity'] = None
                        else:
                            try:
                                norm['Quantity'] = int(vv) if '.' not in vv else float(vv)
                            except Exception:
                                norm['Quantity'] = vv
                    else:
                        norm['Quantity'] = v
                    filled_quantity = True
                    continue

                # default normalization
                if isinstance(v, str):
                    vv = v.strip()
                    norm[header] = None if vv.lower() in ('', 'nan', 'none') else vv
                else:
                    norm[header] = v

            # final safety: check preserved combined key variants
            if not filled_product:
                for candidate_key in ('Order Lines/Quantity', 'Order Lines / Quantity', 'Order Lines - Quantity'):
                    if candidate_key in raw_item and raw_item[candidate_key] not in (None, ''):
                        prod, qty = _extract_product_and_qty_from_string(str(raw_item[candidate_key]))
                        if prod:
                            norm['Product'] = prod
                            filled_product = True
                        if qty is not None and not filled_quantity:
                            try:
                                norm['Quantity'] = int(qty) if '.' not in qty else float(qty)
                            except Exception:
                                norm['Quantity'] = qty
                            filled_quantity = True
                        break

            normalized_items.append(norm)

        items = normalized_items

        # -------------------- Carry-forward Order Reference & Vendor for continuation lines ----
        last_order_ref = None
        last_vendor = None
        for it in items:
            # normalize presence and strip strings
            or_val = it.get('Order Reference')
            v_val = it.get('Vendor')

            if isinstance(or_val, str):
                or_val = or_val.strip() or None
            if isinstance(v_val, str):
                v_val = v_val.strip() or None

            # update last seen if present
            if or_val:
                last_order_ref = or_val
            else:
                # fill missing order ref with last seen (if available)
                if last_order_ref:
                    it['Order Reference'] = last_order_ref

            if v_val:
                last_vendor = v_val
            else:
                # fill missing vendor with last seen (if available)
                if last_vendor:
                    it['Vendor'] = last_vendor
        # --------------------  end carry-forward -----------------------

        # -------------------- Pre-filter missing mandatory rows --------------------
        skipped_rows = []
        filtered_items = []
        for idx, it in enumerate(items, start=1):
            or_val = it.get('Order Reference')
            v_val = it.get('Vendor')
            or_blank = or_val is None or (isinstance(or_val, str) and not or_val.strip())
            v_blank = v_val is None or (isinstance(v_val, str) and not v_val.strip())
            if or_blank or v_blank:
                skipped_rows.append({'row_in_file': idx, 'Order Reference': or_val, 'Vendor': v_val})
            else:
                filtered_items.append(it)
        items = filtered_items

        # -------------------- Process rows --------------------
        row = 0
        imported = 0
        confirmed = 0
        imported_purchaseorders = []
        session_orders = {}  # Track orders created/found in this session by 'Order Reference'
        error_msg = ""
        vendor_added_msg = ""
        warning_msg = ""

        # carry-forward last seen Order Reference across rows
        last_order_ref = None

        if items:
            for item in items:
                row += 1
                vals = {}
                row_not_import_msg = "\n❌Row {rn} not imported.".format(rn=row)
                import_error_msg = ""
                missing_fields_msg = ""
                fields_msg = "\n\tMissing required field(s):"
                vendor_msg = "\n🆕New Vendor(s) added:"

                # Carry-forward Order Reference (if missing in this row)
                if 'Order Reference' in item:
                    or_val = item.get('Order Reference')
                    if isinstance(or_val, str):
                        or_val = or_val.strip() or None
                    if or_val:
                        last_order_ref = or_val
                    else:
                        if last_order_ref:
                            item['Order Reference'] = last_order_ref
                else:
                    if last_order_ref:
                        item['Order Reference'] = last_order_ref

                # Validate required fields (redundant after filter but kept for safety)
                if not item.get('Order Reference'):
                    if missing_fields_msg:
                        missing_fields_msg += "\n\t\t\t\"❗Order Reference\" "
                    else:
                        missing_fields_msg += (fields_msg + "\n\t\t\t\"❗Order Reference\"")
                if item.get('Vendor'):
                    vendor = res_partner.search([('name', '=', item['Vendor'])], limit=1)
                    if not vendor:
                        vendor = res_partner.create({'name': item['Vendor']})
                        vals['partner_id'] = vendor.id
                        if vendor_added_msg:
                            vendor_added_msg += ("\n\t\trow {rn}: {vendor}").format(rn=row, vendor=item['Vendor'])
                        else:
                            vendor_added_msg += (vendor_msg + "\n\t\trow {rn}: \"{vendor}\"").format(rn=row,
                                                                                                     vendor=item[
                                                                                                         'Vendor'])
                    else:
                        vals['partner_id'] = vendor.id
                else:
                    if missing_fields_msg:
                        missing_fields_msg += "\n\t\t\t\"❗Vendor\""
                    else:
                        missing_fields_msg += (fields_msg + "\n\t\t\t\"❗Vendor\"")

                if import_error_msg:
                    import_error_msg += missing_fields_msg
                elif missing_fields_msg:
                    import_error_msg += (row_not_import_msg + missing_fields_msg)
                if import_error_msg:
                    error_msg += import_error_msg
                    continue

                # Optional vendor ref
                if item.get('Vendor Reference'):
                    vals['partner_ref'] = item['Vendor Reference']

                # Order Deadline
                if item.get('Order Deadline'):
                    parsed = self._parse_date_value(item['Order Deadline'])
                    if not parsed:
                        error_msg += row_not_import_msg + (
                            "\n\t\t❎Please check the Order Deadline and supported date formats")
                        continue
                    else:
                        vals['date_order'] = parsed

                # Receipt Date
                if item.get('Receipt Date'):
                    parsed = self._parse_date_value(item['Receipt Date'])
                    if not parsed:
                        error_msg += row_not_import_msg + (
                            "\n\t\t❎Please check the Receipt Date and supported date formats")
                        continue
                    else:
                        vals['date_planned'] = parsed

                if item.get('Purchase Representative'):
                    purchase_representative = res_users.search([('name', '=', item['Purchase Representative'])],
                                                               limit=1)
                    if purchase_representative:
                        vals['user_id'] = purchase_representative.id

                # Find or create purchase order
                order_ref = item.get('Order Reference')
                purchaseorder = session_orders.get(order_ref)

                if not purchaseorder:
                    # In system mode, we only group by what we've seen in THIS session (session_orders)
                    # We do NOT search the database for past imports, because the user wants a NEW system number.
                    if self.order_number == 'from_file':
                        purchaseorder = purchase_order.search([('name', '=', order_ref)], limit=1)

                    if purchaseorder:
                        if vals and purchaseorder.state in ['draft', 'sent', 'to_approve']:
                            purchaseorder.write(vals)
                        session_orders[order_ref] = purchaseorder
                    else:
                        if self.order_number == 'from_system':
                            vals['partner_ref'] = order_ref
                            purchaseorder = purchase_order.create(vals)
                        else:
                            vals['name'] = order_ref
                            purchaseorder = purchase_order.create(vals)
                        session_orders[order_ref] = purchaseorder

                # Prepare line values
                line_vals = {}
                pro_vals = {}

                if item.get('Description'):
                    line_vals['name'] = item['Description']

                # Delivery Date (line)
                if item.get('Delivery Date'):
                    parsed = self._parse_date_value(item['Delivery Date'])
                    if not parsed:
                        error_msg += row_not_import_msg + (
                            "\n\t\t❎Please check the Delivery Date and supported date formats")
                        continue
                    else:
                        line_vals['date_planned'] = parsed

                # Quantity
                if item.get('Quantity'):
                    try:
                        line_vals['product_qty'] = float(item['Quantity'])
                    except Exception:
                        line_vals['product_qty'] = item['Quantity']

                # UoM
                if item.get('Uom'):
                    uom = uom_uom.search([('name', '=', item['Uom'])], limit=1)
                    if uom:
                        pro_vals['uom_id'] = line_vals['product_uom_id'] = uom.id

                # Unit Price
                if item.get('Unit Price'):
                    try:
                        pro_vals['lst_price'] = float(item['Unit Price'])
                        line_vals['price_unit'] = float(item['Unit Price'])
                    except Exception:
                        pro_vals['lst_price'] = item['Unit Price']
                        line_vals['price_unit'] = item['Unit Price']

                # Taxes
                if item.get('Taxes'):
                    tax_name = item['Taxes']
                    m = re.search(r"(\d+)%", str(tax_name))
                    tax_amount = float(m.group(1)) if m else 0.0
                    tax = account_tax.search([('name', '=', tax_name), ('type_tax_use', '=', 'purchase')], limit=1)
                    if not tax:
                        tax = account_tax.create(
                            {'name': tax_name, 'type_tax_use': 'purchase', 'amount': tax_amount if tax_amount else 0.0})
                    pro_vals['taxes_id'] = line_vals['tax_ids'] = [tax.id]

                # Product info
                if item.get('Product'):
                    pro_vals['name'] = item['Product']
                if item.get('Order Reference'):
                    pro_vals['default_code'] = item['Order Reference']

                # ---------------- product resolution (reset per-row) ----------------
                product = False

                if self.import_product_by == 'name':
                    if item.get('Product'):
                        prod_name = item['Product'].strip() if isinstance(item['Product'], str) else item['Product']
                        product = product_product.search([('name', '=', prod_name)], limit=1)
                        if not product:
                            product = product_product.search([('name', 'ilike', prod_name)], limit=1)
                        if not product:
                            pro_vals.setdefault('name', prod_name)
                            product = product_product.create(pro_vals)
                    else:
                        error_msg += row_not_import_msg + ("\n\t❎Product name missing in file!")
                        continue

                elif self.import_product_by == 'default_code':
                    if item.get('Order Reference'):
                        ref = item['Order Reference']
                        product = product_product.search([('default_code', '=', ref)], limit=1)
                        if not product:
                            if not item.get('Product'):
                                warning_msg += (
                                        "\nℹA Product is created with \"Order Reference\" as product name since \"Product\" name is missing at row %d." % row)
                                pro_vals['name'] = ref
                            pro_vals['default_code'] = ref
                            product = product_product.create(pro_vals)
                    else:
                        error_msg += row_not_import_msg + ("\n\t❎Order Reference missing in file!")
                        continue

                elif self.import_product_by == 'barcode':
                    if item.get('Barcode'):
                        bc = str(item['Barcode']).strip()
                        product = product_product.search([('barcode', '=', bc)], limit=1)
                        if not product:
                            if not item.get('Product'):
                                pro_vals.setdefault('name', bc)
                            pro_vals['barcode'] = bc
                            product = product_product.create(pro_vals)
                    else:
                        error_msg += row_not_import_msg + ("\n\t❎Barcode missing in file!")
                        continue

                # attach product to line and write
                if product:
                    line_vals['product_id'] = product.id
                    purchaseorder.write({'order_line': [(0, 0, line_vals)]})
                else:
                    # if no product resolved, skip this row with error
                    error_msg += row_not_import_msg + ("\n\t❎Product resolution failed for this row.")
                    continue

                imported += 1
                imported_purchaseorders.append(purchaseorder)

            # auto-confirm if requested
            if self.auto_confirm_quot and imported_purchaseorders:
                for po in imported_purchaseorders:
                    po.button_confirm()
                    confirmed += 1

        # Compose missing rows message
        if skipped_rows:
            mr_msgs = []
            for r in skipped_rows:
                mr_msgs.append("Row %d skipped: missing Order Reference or Vendor" % r['row_in_file'])
            missing_info_msg = "\n\n⚠ The following rows were skipped because they were missing mandatory fields:\n" + "\n".join(
                mr_msgs)
        else:
            missing_info_msg = ""

        # Show errors if any
        if error_msg:
            error_msg = "\n\n⚠ WARNING ⚠" + error_msg
            if missing_info_msg:
                error_msg += missing_info_msg
            error_message = self.env['import.message'].create({'message': error_msg})
            return {
                'name': 'Error!',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'import.message',
                'res_id': error_message.id,
                'target': 'new'
            }

        # Success message
        processed_names = ", ".join(list(set(po.name for po in imported_purchaseorders if po.name)))
        msg = (("Imported %d records.\nConfirmed %d records" % (imported, confirmed)) + vendor_added_msg + warning_msg)
        if processed_names:
            msg += f"\n\nOrders processed (Created/Updated): {processed_names}"
        message = self.env['import.message'].create({'message': msg})
        if message:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': msg,
                    'type': 'rainbow_man',
                }
            }
