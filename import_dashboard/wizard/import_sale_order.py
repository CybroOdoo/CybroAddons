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
import logging
import base64
import binascii
import csv
import io
import os
import tempfile
import xlrd
import openpyxl
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

    DATE_PATTERNS = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y",
        "%Y.%m.%d", "%d.%m.%Y", "%m.%d.%Y",
        "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
        "%Y/%m/%d", "%Y %m %d"
    ]

    def _parse_date_value(self, value):
        import datetime, re
        if value is None:
            return False
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime.combine(value, datetime.time())
        if isinstance(value, (int, float)):
            try:
                base = datetime.datetime(1899, 12, 30)
                return base + datetime.timedelta(days=float(value))
            except Exception:
                pass
        s = str(value).strip()
        if not s:
            return False
        try:
            return datetime.datetime.fromisoformat(s)
        except Exception:
            pass
        try:
            user_lang = getattr(self.env.user, 'lang', None)
            if user_lang:
                lang = self.env['res.lang'].search([('code', '=', user_lang)], limit=1)
                lang_fmt = getattr(lang, 'date_format', None)
                if lang_fmt:
                    try:
                        return datetime.datetime.strptime(s, lang_fmt)
                    except Exception:
                        pass
        except Exception:
            pass
        for fmt in self.DATE_PATTERNS:
            try:
                return datetime.datetime.strptime(s, fmt)
            except Exception:
                continue
        # last resort permutations
        try:
            parts = re.split(r"[-/\. ]", s)
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%Y-%m-%d"):
                    try:
                        return datetime.datetime.strptime(s, fmt)
                    except Exception:
                        pass
        except Exception:
            pass
        return False

    def action_import_sale_order(self):
        """Creating sale order record using uploaded xl/csv files"""
        _logger = logging.getLogger(__name__)
        _logger.info("Importing sale orders...")
        sale_order = self.env['sale.order']
        res_partner = self.env['res.partner']
        res_users = self.env['res.users']
        product_product = self.env['product.product']
        account_tax = self.env['account.tax']
        uom_uom = self.env['uom.uom']

        debug_log = "/tmp/odoo_import_sale_order_debug.log"
        with open(debug_log, "w") as f:
            f.write(f"Starting import at {fields.Datetime.now()}\n")
            f.write(f"Database: {self._cr.dbname}\n")
            f.write(f"File Type: {self.file_type}\n")
            f.write(f"Order Number mode: {self.order_number}\n")
            f.write(f"Product mode: {self.import_product_by}\n")
        _logger.info(
            f"File Type: {self.file_type}, Order Number mode: {self.order_number}, Product mode: {self.import_product_by}")

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
                    "File not Valid.\n\nPlease check the type and format of "
                    "the file and try again!")
        elif self.file_type == 'xlsx':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload or b''))
                fp.flush()
                fp.close()
                workbook = openpyxl.load_workbook(fp.name, data_only=True)
                sheet = workbook.active
            except Exception as e:
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

        with open(debug_log, "a") as f:
            f.write(f"Items count after reading file: {len(items)}\n")
            if items:
                f.write(f"First item keys: {list(items[0].keys())}\n")

        # Defensive: ensure items is a list
        if not items:
            items = []
        elif not isinstance(items, list):
            try:
                items = list(items)
            except Exception:
                pass

        # -------------------- Normalization (Product / Quantity parsing) --------------------
        import re as _re

        def _extract_prod_qty(s):
            """Return (product_name, qty_or_None)."""
            if s is None:
                return (None, None)
            s = str(s).strip()
            if not s:
                return (None, None)
            parts = _re.split(r'\s*[\/|\-]\s*', s)
            if len(parts) >= 2 and _re.fullmatch(r'\d+(\.\d+)?', parts[-1].strip()):
                qty = parts[-1].strip()
                prod = '/'.join(parts[:-1]).strip()
                return (prod, qty)
            m = _re.search(r'^(?P<prod>.*?)[\s\(\[]*[xX]?\s*(?P<qty>\d+(\.\d+)?)\s*[\)\]]*$', s)
            if m:
                prod = m.group('prod').strip()
                qty = m.group('qty').strip()
                if prod == '':
                    return (None, qty)
                return (prod, qty)
            # reversed e.g., "10 / Product Name"
            parts_rev = _re.split(r'\s*[\/|\-]\s*', s)
            if len(parts_rev) >= 2 and _re.fullmatch(r'\d+(\.\d+)?', parts_rev[0].strip()):
                qty = parts_rev[0].strip()
                prod = '/'.join(parts_rev[1:]).strip()
                return (prod, qty)
            return (s, None)

        def normalize_product_cell(cell):
            """
            Extract bracketed tokens and a cleaned product name.
            Example:
                "[S00059] [FURN_6666] Acoustic Bloc Screens (White)"
            -> ( "Acoustic Bloc Screens (White)", ["S00059","FURN_6666"] )
            Non-bracketed strings return (cleaned_string, []).
            """
            if cell is None:
                return (None, [])
            s = str(cell).strip()
            if not s:
                return (None, [])
            # find bracketed tokens
            codes = _re.findall(r'\[([^\]]+)\]', s)
            # remove bracketed blocks from string
            cleaned = _re.sub(r'\[.*?\]', '', s).strip()
            # also collapse multiple spaces
            cleaned = _re.sub(r'\s{2,}', ' ', cleaned).strip()
            return (cleaned or None, codes)

        normalized_items = []
        for raw_item in items:
            if not isinstance(raw_item, dict):
                normalized_items.append(raw_item)
                continue
            norm = {}
            filled_product = False
            filled_quantity = False

            for k, v in raw_item.items():
                if k is None:
                    continue
                header = k.strip() if isinstance(k, str) else k
                header_l = header.lower() if isinstance(header, str) else ''

                # Combined Order Lines / Quantity columns
                if isinstance(header, str) and header_l.startswith('order lines'):
                    value = v if not (isinstance(v, str) and v.strip().lower() in ('nan', 'none')) else None
                    if isinstance(value, str):
                        prod, qty = _extract_prod_qty(value)
                        if prod:
                            norm['Product'] = prod
                            filled_product = True
                        if qty is not None:
                            try:
                                norm['Quantity'] = int(qty) if '.' not in qty else float(qty)
                            except Exception:
                                norm['Quantity'] = qty
                            filled_quantity = True
                        if not prod and value:
                            norm['Product'] = value
                            filled_product = True
                    elif isinstance(value, (int, float)):
                        norm['Quantity'] = value
                        filled_quantity = True
                    else:
                        norm[header] = value
                    continue

                # Explicit Product header
                if isinstance(header, str) and header_l == 'product':
                    if isinstance(v, str):
                        vv = v.strip()
                        # Normalize product cell here as well: extract bracket tokens if present
                        prod_name, codes = normalize_product_cell(vv)
                        if prod_name:
                            norm['Product'] = prod_name
                        else:
                            norm['Product'] = None
                        # preserve raw codes for later use
                        if codes:
                            norm.setdefault('_product_codes', codes)
                    else:
                        norm['Product'] = v
                    filled_product = True
                    continue

                # Explicit Quantity header
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

                # default normalization: strip strings, convert blank-like to None
                if isinstance(v, str):
                    vv = v.strip()
                    norm[header] = None if vv.lower() in ('', 'nan', 'none') else vv
                else:
                    norm[header] = v

            # last chance: if no product yet, check typical combined keys
            if not filled_product:
                for candidate_key in ('Order Lines/Quantity', 'Order Lines / Quantity', 'Order Lines - Quantity'):
                    if candidate_key in raw_item and raw_item[candidate_key] not in (None, ''):
                        prod, qty = _extract_prod_qty(str(raw_item[candidate_key]))
                        if prod:
                            norm['Product'] = prod
                        if qty is not None and not filled_quantity:
                            try:
                                norm['Quantity'] = int(qty) if '.' not in qty else float(qty)
                            except Exception:
                                norm['Quantity'] = qty
                        break

            normalized_items.append(norm)

        items = normalized_items

        # -------------------- Carry-forward Order Reference & Customer --------------------
        last_order_ref = None
        last_customer = None
        for it in items:
            orv = it.get('Order Reference')
            cv = it.get('Customer')
            if isinstance(orv, str):
                orv = orv.strip() or None
            if isinstance(cv, str):
                cv = cv.strip() or None
            if orv:
                last_order_ref = orv
            else:
                if last_order_ref:
                    it['Order Reference'] = last_order_ref
            if cv:
                last_customer = cv
            else:
                if last_customer:
                    it['Customer'] = last_customer

        # -------------------- Remove rows with no product (they can't become order lines) --------------------
        cleaned_items = []
        for it in items:
            prod = it.get('Product')
            if prod is None:
                continue
            if isinstance(prod, str) and prod.strip() == '':
                continue
            cleaned_items.append(it)
        items = cleaned_items

        # -------------------- Process rows --------------------
        row = 0
        imported = 0
        confirmed = 0
        imported_saleorders = []
        session_orders = {}  # Track orders created/found in this session by 'Order Reference'
        error_msg = ""
        cust_added_msg = ""
        warning_msg = ""

        if items:
            with open(debug_log, "a") as f:
                f.write(f"Items count after normalization: {len(items)}\n")
            for item in items:
                row += 1
                with open(debug_log, "a") as f:
                    f.write(
                        f"Processing row {row}: Order Ref='{item.get('Order Reference')}', Product='{item.get('Product')}'\n")
                vals = {}
                row_not_import_msg = "\n◼  Row {rn} not imported.".format(rn=row)
                import_error_msg = ""
                missing_fields_msg = ""
                fields_msg = "\n\t\tMissing required field(s):"
                cust_msg = "\nNew Customer(s) added:"

                # Double-check/validate Order Reference (should be filled by carry-forward)
                if not item.get('Order Reference'):
                    if missing_fields_msg:
                        missing_fields_msg += "\n\t\t\t\"Order Reference\" "
                    else:
                        missing_fields_msg += (fields_msg + "\n\t\t\t\"Order Reference\"")

                # Customer handling (use limit=1 to avoid ambiguous recordsets)
                if item.get('Customer'):
                    customer = res_partner.search([('name', '=', item['Customer'])], limit=1)
                    if not customer:
                        customer = res_partner.create({'name': item['Customer']})
                        vals['partner_id'] = customer.id
                        if cust_added_msg:
                            cust_added_msg += ("\n\t\trow {rn}: {cust}").format(rn=row, cust=item['Customer'])
                        else:
                            cust_added_msg += (cust_msg + "\n\t\trow {rn}: \"{cust}\"").format(rn=row,
                                                                                               cust=item['Customer'])
                    else:
                        vals['partner_id'] = customer.id
                else:
                    if missing_fields_msg:
                        missing_fields_msg += "\n\t\t\t\"Customer\""
                    else:
                        missing_fields_msg += (fields_msg + "\n\t\t\t\"Customer\"")

                # Compose import_error_msg
                if import_error_msg:
                    import_error_msg += missing_fields_msg
                elif missing_fields_msg:
                    import_error_msg += (row_not_import_msg + missing_fields_msg)

                # Quotation Date parsing using robust helper (if helper exists in the class)
                if item.get('Quotation Date'):
                    try:
                        parsed = self._parse_date_value(item['Quotation Date'])
                    except Exception:
                        parsed = False
                    if not parsed:
                        if import_error_msg:
                            import_error_msg += ("\n\t\t Please check the Quotation Date and supported formats")
                        else:
                            import_error_msg += row_not_import_msg + (
                                "\n\t\t⚠ Please check the Quotation Date and supported formats")
                    else:
                        vals['date_order'] = parsed

                if import_error_msg:
                    error_msg += import_error_msg
                    continue

                # Salesperson
                if item.get('Salesperson'):
                    sales_person = res_users.search([('name', '=', item['Salesperson'])], limit=1)
                    if sales_person:
                        vals['user_id'] = sales_person.id

                # Find or create sale order
                order_ref = item.get('Order Reference')
                saleorder = session_orders.get(order_ref)
                found = bool(saleorder)

                if not saleorder:
                    # In system mode, we only group by what we've seen in THIS session (session_orders)
                    # We do NOT search the database for past imports, because the user wants a NEW system number.
                    if self.order_number == 'from_file':
                        saleorder = sale_order.search([('name', '=', order_ref)], limit=1)

                    found = bool(saleorder)
                    if saleorder:
                        if vals and saleorder.state in ['draft', 'sent']:
                            saleorder.write(vals)
                        session_orders[order_ref] = saleorder
                    else:
                        if self.order_number == 'from_system':
                            vals['client_order_ref'] = order_ref
                            saleorder = sale_order.create(vals)
                        else:
                            vals['name'] = order_ref
                            saleorder = sale_order.create(vals)
                        session_orders[order_ref] = saleorder

                with open(debug_log, "a") as f:
                    f.write(
                        f"Sale Order: {saleorder.name} (ID: {saleorder.id}) - {'Found' if found else 'Created'}, State: {saleorder.state}, Company: {saleorder.company_id.name} (ID: {saleorder.company_id.id})\n")
                _logger.info(
                    f"Sale Order: {saleorder.name} (ID: {saleorder.id}) - {'Found' if found else 'Created'}, State: {saleorder.state}, Company: {saleorder.company_id.name}")

                # Prepare line values
                line_vals = {}
                pro_vals = {}
                if item.get('Description'):
                    line_vals['name'] = item['Description']
                if item.get('Quantity'):
                    try:
                        line_vals['product_uom_qty'] = float(item['Quantity'])
                    except Exception:
                        line_vals['product_uom_qty'] = item['Quantity']
                if item.get('Uom'):
                    uom = uom_uom.search([('name', '=', item['Uom'])], limit=1)
                    if uom:
                        pro_vals['uom_id'] = line_vals['product_uom_id'] = uom.id
                if item.get('Unit Price'):
                    try:
                        pro_vals['lst_price'] = float(item['Unit Price'])
                        line_vals['price_unit'] = float(item['Unit Price'])
                    except Exception:
                        pro_vals['lst_price'] = item['Unit Price']
                        line_vals['price_unit'] = item['Unit Price']
                if item.get('Taxes'):
                    tax_name = item['Taxes']
                    m = _re.findall(r"(\d+)%", str(tax_name))
                    tax_amount = float(m[0]) if m else 0.0
                    tax = account_tax.search([('name', '=', tax_name), ('type_tax_use', '=', 'sale')], limit=1)
                    if not tax:
                        tax = account_tax.create({
                            'name': tax_name,
                            'type_tax_use': 'sale',
                            'amount': tax_amount if tax_amount else 0.0
                        })
                    pro_vals['taxes_id'] = line_vals['tax_ids'] = [tax.id]
                if item.get('Disc.%'):
                    line_vals['discount'] = item['Disc.%']

                # Product meta: use normalize_product_cell to extract bracketed codes if present
                if item.get('Product'):
                    # try to extract product name and bracketed tokens
                    clean_name, codes = normalize_product_cell(item['Product'])
                    if clean_name:
                        pro_vals['name'] = clean_name
                    else:
                        # fallback to raw value
                        pro_vals['name'] = item['Product']
                    # pick a candidate default_code from bracketed tokens (prefer tokens that look like codes)
                    if codes:
                        # choose the last token that looks like an internal code (alphanumeric + _ or -)
                        candidate = None
                        for c in reversed(codes):
                            if _re.fullmatch(r'[A-Za-z0-9_\-]+', c.strip()):
                                candidate = c.strip()
                                break
                        if candidate:
                            pro_vals['default_code'] = candidate

                # if Order Reference present set as default_code if not already set
                if item.get('Order Reference') and not pro_vals.get('default_code'):
                    pro_vals['default_code'] = item['Order Reference']

                # ---------------- product resolution (reset per-row) ----------------
                product = False

                if self.import_product_by == 'name':
                    if pro_vals.get('name'):
                        prod_name = pro_vals['name']
                        product = product_product.search([('name', '=', prod_name)], limit=1)
                        if not product:
                            product = product_product.search([('name', 'ilike', prod_name)], limit=1)
                        if not product:
                            # if default_code exists, set it on creation
                            product = product_product.create(pro_vals)
                    else:
                        error_msg += row_not_import_msg + ("\n\t⚠ Product name missing in file!")
                        continue

                elif self.import_product_by == 'default_code':
                    # match by product default_code (we consider Order Reference or extracted code)
                    ref = item.get('Order Reference') or pro_vals.get('default_code')
                    if ref:
                        product = product_product.search([('default_code', '=', ref)], limit=1)
                        if not product:
                            # create only if we have at least a product name or a reference
                            if not pro_vals.get('name'):
                                # use ref as name if name missing
                                pro_vals.setdefault('name', ref)
                            pro_vals['default_code'] = ref
                            product = product_product.create(pro_vals)
                    else:
                        error_msg += row_not_import_msg + ("\n\t⚠ Order Reference / default code missing in file!")
                        continue

                elif self.import_product_by == 'barcode':
                    if item.get('Barcode'):
                        bc = str(item['Barcode']).strip()
                        product = product_product.search([('barcode', '=', bc)], limit=1)
                        if not product:
                            if not pro_vals.get('name'):
                                pro_vals.setdefault('name', bc)
                            pro_vals['barcode'] = bc
                            product = product_product.create(pro_vals)
                    else:
                        error_msg += row_not_import_msg + ("\n\t⚠ Barcode missing in file!")
                        continue

                # ---------------- price fallback from existing product ----------------
                # Normalize product variable to single record if it's a recordset
                if product:
                    # if product is a recordset with many records, keep the first to avoid ambiguity
                    if hasattr(product, '__len__') and len(product) > 1:
                        product = product[0]

                # Only try to fetch DB price when a product exists
                if product:
                    try:
                        db_price = product.lst_price if hasattr(product, 'lst_price') else None
                        # treat empty/zero/None as "no price provided" from Excel
                        price_provided = 'price_unit' in line_vals and line_vals.get('price_unit') not in (None, '', 0,
                                                                                                           0.0)
                        # If Excel did not provide price (or it's zero/blank), use product's list price when available
                        if not price_provided and db_price not in (None, ''):
                            try:
                                line_vals['price_unit'] = float(db_price)
                            except Exception:
                                # fallback to raw db_price if float cast fails
                                line_vals['price_unit'] = db_price
                            # also keep product template/list price in pro_vals for product creation/update
                            try:
                                pro_vals['lst_price'] = float(db_price)
                            except Exception:
                                pro_vals['lst_price'] = db_price
                    except Exception:
                        # safety: do nothing if reading price fails for any reason
                        pass
                # ---------------- end price fallback ---------------

                # attach product to line and write
                if product:
                    line_vals['product_id'] = product.id
                    saleorder.write({'order_line': [(0, 0, line_vals)]})
                    with open(debug_log, "a") as f:
                        f.write(
                            f"  Line added: {line_vals.get('name')}, Product ID: {product.id}, Current Line count: {len(saleorder.order_line)}\n")
                else:
                    error_msg += row_not_import_msg + ("\n\t⚠ Product resolution failed for this row.")
                    continue

                imported += 1
                imported_saleorders.append(saleorder)
                with open(debug_log, "a") as f:
                    f.write(f"Row {row} imported successfully. Total imported: {imported}\n")
                _logger.info(f"Row {row} imported. Total: {imported}")

            # auto-confirm if requested
            if self.auto_confirm_quot and imported_saleorders:
                for so in imported_saleorders:
                    so.action_confirm()
                    confirmed += 1

        # Show errors if any
        if error_msg:
            error_msg = "\n\nWARNING" + error_msg
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
        processed_names = ", ".join(list(set(so.name for so in imported_saleorders if so.name)))
        msg = (("Imported %d records.\nConfirmed %d records" % (imported, confirmed)) + cust_added_msg + warning_msg)
        if processed_names:
            msg += f"\n\nOrders processed (Created/Updated): {processed_names}"

        with open(debug_log, "a") as f:
            f.write(f"Final Message: {msg}\n")
        message = self.env['import.message'].create({'message': msg})
        if message:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': msg,
                    'type': 'rainbow_man',
                }
            }
