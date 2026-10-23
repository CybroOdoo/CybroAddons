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
import datetime
import logging
import re
from .import_utils import get_file_content, read_csv_data, read_xlsx_data
from odoo.exceptions import ValidationError
from odoo import fields, models

_logger = logging.getLogger(__name__)


class ImportSaleOrder(models.TransientModel):
    """ Model for import sale orders. """
    _name = 'import.sale.order'
    _description = 'Sale Order Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xlsx', 'XLSX File')],
        string='Select File Type', default='csv', help='Type of the file to import')
    file_upload = fields.Binary(string="Upload File",
                                help="File to import")
    auto_confirm_quot = fields.Boolean(
        string='Confirm Quotation Automatically',
        help='Automatically confirm the quotation')
    order_number = fields.Selection(
        selection=[('from_system', 'From System'),
                   ('from_file', 'From File')],
        string='Order / Quotation Number', default='from_file',
        help='Take the order number from the file or from the system sequence')
    import_product_by = fields.Selection(
        selection=[('name', 'Name'),
                   ('default_code', 'Internal Reference'),
                   ('barcode', 'Barcode')], default='name',
        string="Match Products By", help="Product field used to match the products in the file")

    DATE_PATTERNS = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y",
        "%Y.%m.%d", "%d.%m.%Y", "%m.%d.%Y",
        "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
        "%Y/%m/%d", "%Y %m %d"
    ]

    def _parse_date_value(self, value):
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
                _logger.debug("Could not parse date value %r", value, exc_info=True)
        s = str(value).strip()
        if not s:
            return False
        try:
            return datetime.datetime.fromisoformat(s)
        except Exception:
            _logger.debug("Could not parse date value %r", value, exc_info=True)
        try:
            user_lang = getattr(self.env.user, 'lang', None)
            if user_lang:
                lang = self.env['res.lang'].search([('code', '=', user_lang)], limit=1)
                lang_fmt = getattr(lang, 'date_format', None)
                if lang_fmt:
                    try:
                        return datetime.datetime.strptime(s, lang_fmt)
                    except Exception:
                        _logger.debug("Could not parse date value %r", value, exc_info=True)
        except Exception:
            _logger.debug("Could not parse date value %r", value, exc_info=True)
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
                        _logger.debug("Could not parse date value %r", value, exc_info=True)
        except Exception:
            _logger.debug("Could not parse date value %r", value, exc_info=True)
        return False

    def action_import_sale_order(self):
        """Creating sale order record using uploaded xl/csv files"""
        _logger.info("Importing sale orders...")
        sale_order = self.env['sale.order']
        res_partner = self.env['res.partner']
        res_users = self.env['res.users']
        product_product = self.env['product.product']
        account_tax = self.env['account.tax']
        uom_uom = self.env['uom.uom']

        _logger.info(
            "File Type: %s, Order Number mode: %s, Product mode: %s",
            self.file_type, self.order_number, self.import_product_by)

        # Read file into items (list of dicts)
        items = []
        if self.file_type == 'csv':
            try:
                items = read_csv_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the type and format of "
                               "the file and try again!"))
        elif self.file_type == 'xlsx':
            try:
                items = read_xlsx_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the type and format of "
                               "the file and try again!"))

        # Make sure items is a list
        if not items:
            items = []
        elif not isinstance(items, list):
            try:
                items = list(items)
            except Exception:
                _logger.debug("Could not convert imported items to a list", exc_info=True)

        # Normalization (Product / Quantity parsing)
        def _extract_prod_qty(s):
            """Return (product_name, qty_or_None)."""
            if s is None:
                return (None, None)
            s = str(s).strip()
            if not s:
                return (None, None)
            parts = re.split(r'\s*[\/|\-]\s*', s)
            if len(parts) >= 2 and re.fullmatch(r'\d+(\.\d+)?', parts[-1].strip()):
                qty = parts[-1].strip()
                prod = '/'.join(parts[:-1]).strip()
                return (prod, qty)
            m = re.search(r'^(?P<prod>.*?)[\s\(\[]*[xX]?\s*(?P<qty>\d+(\.\d+)?)\s*[\)\]]*$', s)
            if m:
                prod = m.group('prod').strip()
                qty = m.group('qty').strip()
                if prod == '':
                    return (None, qty)
                return (prod, qty)
            # reversed e.g., "10 / Product Name"
            parts_rev = re.split(r'\s*[\/|\-]\s*', s)
            if len(parts_rev) >= 2 and re.fullmatch(r'\d+(\.\d+)?', parts_rev[0].strip()):
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
            codes = re.findall(r'\[([^\]]+)\]', s)
            # remove bracketed blocks from string
            cleaned = re.sub(r'\[.*?\]', '', s).strip()
            # also collapse multiple spaces
            cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
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

        # Carry-forward Order Reference & Customer
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

        # Remove rows with no product (they can't become order lines)
        cleaned_items = []
        for it in items:
            prod = it.get('Product')
            if prod is None:
                continue
            if isinstance(prod, str) and prod.strip() == '':
                continue
            cleaned_items.append(it)
        items = cleaned_items

        # Process rows
        row = 0
        imported = 0
        confirmed = 0
        imported_saleorders = []
        session_orders = {}  # Track orders created/found in this session by 'Order Reference'
        error_msg = ""
        cust_added_msg = ""
        warning_msg = ""

        if items:
            for item in items:
                row += 1
                vals = {}
                row_not_import_msg = self.env._("\n◼  Row %(rn)s not imported.", rn=row)
                import_error_msg = ""
                missing_fields_msg = ""
                fields_msg = self.env._("\n\t\tMissing required field(s):")
                cust_msg = self.env._("\nNew Customer(s) added:")

                # Double-check/validate Order Reference (should be filled by carry-forward)
                if not item.get('Order Reference'):
                    if missing_fields_msg:
                        missing_fields_msg += self.env._("\n\t\t\t\"Order Reference\" ")
                    else:
                        missing_fields_msg += (fields_msg + self.env._("\n\t\t\t\"Order Reference\""))

                # Customer handling (use limit=1 to avoid ambiguous recordsets)
                if item.get('Customer'):
                    customer = res_partner.search([('name', '=', item['Customer'])], limit=1)
                    if not customer:
                        customer = res_partner.create({'name': item['Customer']})
                        vals['partner_id'] = customer.id
                        if cust_added_msg:
                            cust_added_msg += self.env._("\n\t\trow %(rn)s: %(cust)s", rn=row, cust=item['Customer'])
                        else:
                            cust_added_msg += (cust_msg + "\n\t\trow {rn}: \"{cust}\"").format(rn=row,
                                                                                               cust=item['Customer'])
                    else:
                        vals['partner_id'] = customer.id
                else:
                    if missing_fields_msg:
                        missing_fields_msg += self.env._("\n\t\t\t\"Customer\"")
                    else:
                        missing_fields_msg += (fields_msg + self.env._("\n\t\t\t\"Customer\""))

                # Compose import_error_msg
                if import_error_msg:
                    import_error_msg += missing_fields_msg
                elif missing_fields_msg:
                    import_error_msg += (row_not_import_msg + missing_fields_msg)

                # Quotation Date
                if item.get('Quotation Date'):
                    try:
                        parsed = self._parse_date_value(item['Quotation Date'])
                    except Exception:
                        parsed = False
                    if not parsed:
                        if import_error_msg:
                            import_error_msg += (self.env._("\n\t\t Please check the Quotation Date and supported formats"))
                        else:
                            import_error_msg += row_not_import_msg + (
                                self.env._("\n\t\t⚠ Please check the Quotation Date and supported formats"))
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
                    # With system numbering, rows are grouped only within this file;
                    # existing orders are never reused
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

                _logger.info(
                    "Sale Order: %s (ID: %s) - %s, State: %s, Company: %s",
                    saleorder.name, saleorder.id, 'Found' if found else 'Created',
                    saleorder.state, saleorder.company_id.name)

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
                    m = re.findall(r"(\d+)%", str(tax_name))
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
                            if re.fullmatch(r'[A-Za-z0-9_\-]+', c.strip()):
                                candidate = c.strip()
                                break
                        if candidate:
                            pro_vals['default_code'] = candidate

                # if Order Reference present set as default_code if not already set
                if item.get('Order Reference') and not pro_vals.get('default_code'):
                    pro_vals['default_code'] = item['Order Reference']

                # Product resolution (reset per-row)
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
                        error_msg += row_not_import_msg + (self.env._("\n\t⚠ Product name missing in file!"))
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
                        error_msg += row_not_import_msg + (self.env._("\n\t⚠ Order Reference / default code missing in file!"))
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
                        error_msg += row_not_import_msg + (self.env._("\n\t⚠ Barcode missing in file!"))
                        continue

                # Price fallback from existing product
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
                        # The price lookup is optional; keep the row if it fails
                        _logger.debug("Could not read product price for row %s", row, exc_info=True)

                # attach product to line and write
                if product:
                    line_vals['product_id'] = product.id
                    saleorder.write({'order_line': [(0, 0, line_vals)]})
                else:
                    error_msg += row_not_import_msg + (self.env._("\n\t⚠ Product resolution failed for this row."))
                    continue

                imported += 1
                imported_saleorders.append(saleorder)
                _logger.info("Row %s imported. Total: %s", row, imported)

            # auto-confirm if requested
            if self.auto_confirm_quot and imported_saleorders:
                for so in imported_saleorders:
                    so.action_confirm()
                    confirmed += 1

        # Show errors if any
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
        processed_names = ", ".join(list(set(so.name for so in imported_saleorders if so.name)))
        msg = ((self.env._("Imported %(imported)d records.\nConfirmed %(confirmed)d records", imported=imported, confirmed=confirmed)) + cust_added_msg + warning_msg)
        if processed_names:
            msg += self.env._("\n\nOrders processed (Created/Updated): %(processed_names)s", processed_names=processed_names)

        message = self.env['import.message'].create({'message': msg})
        if message:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': msg,
                    'type': 'rainbow_man',
                }
            }
