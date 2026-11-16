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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import io
import logging
import re
from datetime import datetime

import pytesseract
from pdf2image import convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError,
)
from PIL import Image, UnidentifiedImageError

from odoo import Command, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class DigitizeBill(models.TransientModel):
    """Wizard to extract bill text via OCR and generate a draft vendor bill."""

    _name = "digitize.bill"
    _description = "Digitize Bill"

    bill = fields.Binary(
        string="Document",
        required=True,
        help="Choose a scanned document",
    )
    file_name = fields.Char(help="Name of the file")

    @api.model
    def is_digitize_bill_enabled(self):
        """Return whether bill digitization is enabled in settings."""
        return bool(
            self.env['ir.config_parameter'].sudo().get_bool(
                'bill_digitization.digitize_bill',
            ),
        )

    def _try_parse_bounded_float(self, raw_value):
        """Parse a numeric string if within range, else return None."""
        try:
            parsed = float(raw_value)
        except (ValueError, TypeError):
            return None
        return 0.0 if parsed > 999999999 else parsed

    def clean_number(self, value):
        """Normalize OCR numeric strings into a bounded float."""
        if not value:
            return 0.0

        original_value = str(value).strip()
        if not re.search(r'\d', original_value):
            return 0.0

        letter_count = len(re.findall(r'[a-zA-Z]', original_value))
        digit_count = len(re.findall(r'\d', original_value))
        if letter_count > digit_count:
            return 0.0

        if not re.match(r'^[\d\s\.,\$\-\(\)O0oIl]+$', original_value):
            return 0.0

        cleaned = (
            original_value.replace(',', '')
            .replace(' ', '')
            .replace('$', '')
            .replace('Rs', '')
            .replace('₹', '')
            .replace(')', '0')
            .replace('(', '')
            .replace('O', '0')
            .replace('o', '0')
            .replace('l', '1')
            .replace('I', '1')
        )
        cleaned = re.sub(r'\.{2,}', '.', cleaned)

        if '.' not in cleaned and cleaned.count('-') == 1:
            parts = cleaned.split('-')
            if (
                len(parts) == 2
                and parts[0].isdigit()
                and parts[1].isdigit()
                and len(parts[1]) <= 2
            ):
                cleaned = f"{parts[0]}.{parts[1]}"

        cleaned = re.sub(r'[^\d.\-]', '', cleaned)
        parts = cleaned.split('.')
        if len(parts) > 2:
            cleaned = f"{parts[0]}.{''.join(parts[1:])}"

        cleaned = cleaned.strip('.-')
        if not cleaned or not re.search(r'\d', cleaned):
            return 0.0

        direct_float = self._try_parse_bounded_float(cleaned)
        if direct_float is not None:
            return direct_float

        numbers = re.findall(r'\d+\.?\d*', cleaned)
        if numbers:
            fallback_float = self._try_parse_bounded_float(numbers[0])
            if fallback_float is not None:
                return fallback_float
        return 0.0

    def clean_product_name(self, product_name):
        """Strip bracketed codes, line breaks, and noise from product text."""
        name = product_name.strip()
        if '\n' in name:
            name = name.split('\n')[-1].strip()
        if '\r' in name:
            name = name.split('\r')[-1].strip()

        name = re.sub(r'\(.*?\)', '', name)
        name = re.sub(r'\[.*?\]', '', name)
        name = re.sub(r'[_\|]', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        return name.strip(' ,-')

    def is_likely_address(self, product_name):
        """Return True if the extracted text looks like a postal address."""
        name_lower = product_name.lower().strip()

        if product_name.count(',') >= 2:
            parts = [part.strip() for part in product_name.split(',') if part.strip()]
            has_short_parts = any(len(part) <= 4 for part in parts)
            has_numbers = any(re.search(r'\d{4,}', part) for part in parts)
            if has_short_parts or has_numbers:
                return True

            is_likely_product = all(
                len(part) > 3 and part[0].isupper()
                for part in parts
            )
            if not is_likely_product:
                return True

        address_patterns = (
            r'\b\d{5}(-\d{4})?\b',
            r'\b[A-Z]{2}\s+\d{5}\b',
            r'\bstreet\b',
            r'\bavenue\b',
            r'\broad\b',
            r'\bblvd\b',
            r'\bapt\b',
            r'\bsuite\b',
            r'\bunit\b',
            r'\bfloor\b',
            r'\bpo box\b',
            r'\bp\.o\.\s*box\b',
        )
        return any(re.search(pattern, name_lower) for pattern in address_patterns)

    def is_valid_product_line(self, product_name):
        """Return True when cleaned text looks like a product line."""
        if not product_name or len(product_name) < 3:
            return False

        name_lower = product_name.lower().strip()
        skip_patterns = (
            r'^\s*invoice\b',
            r'^\s*bill\b',
            r'^\s*receipt\b',
            r'^\s*total\b',
            r'^\s*subtotal\b',
            r'^\s*tax\b',
            r'^\s*amount\b',
            r'^\s*description\b',
            r'^\s*qty\b',
            r'^\s*quantity\b',
            r'^\s*price\b',
            r'^\s*unit\b',
            r'^\s*item\b',
            r'^\s*product\b',
            r'^\s*date\b',
            r'^\s*customer\b',
            r'^\s*vendor\b',
            r'^\s*phone\b',
            r'^\s*mobile\b',
            r'^\s*email\b',
            r'^\s*website\b',
            r'^\s*payment\b',
            r'^\s*terms\b',
            r'^\s*account\b',
            r'^\s*bank\b',
            r'^\s*page\b',
            r'^\s*signature\b',
            r'^\s*discount\b',
            r'^\s*grand\b',
            r'^\s*comments\b',
            r'^\s*salesperson\b',
            r'^\s*reference\b',
            r'^\s*balance\b',
            r'^\s*due\b',
            r'^\s*address\b',
        )
        if any(re.search(pattern, name_lower) for pattern in skip_patterns):
            return False

        stop_phrases = (
            'ship to',
            'bill to',
            'sold to',
            'thank you',
            'p.o. number',
            'due date',
            'due after',
            'payment reference',
        )
        if any(phrase in name_lower for phrase in stop_phrases):
            return False

        if self.is_likely_address(product_name):
            return False

        words = product_name.split()
        if len(words) >= 3 and len(set(words)) / len(words) < 0.6:
            return False

        if len(re.findall(r'[A-Za-z0-9]', product_name)) < len(product_name) * 0.5:
            return False

        return len(product_name) <= 100

    def _infer_qty_price_from_three(self, numbers):
        """Disambiguate (qty, price) when qty, price, and subtotal exist."""
        first, second, third = numbers[0], numbers[1], numbers[2]
        expected_total = first * second
        tolerance = max(0.1, expected_total * 0.01)

        if abs(third - expected_total) < tolerance:
            return first, second
        if first <= 100 and first % 1 == 0 and second % 1 != 0:
            return first, second
        if second <= 100 and second % 1 == 0 and first % 1 != 0:
            return second, first
        return first, second

    def _infer_qty_price(self, numbers, prefer_smaller_qty=False):
        """Infer (quantity, unit_price) from extracted numeric tokens."""
        if len(numbers) >= 3:
            return self._infer_qty_price_from_three(numbers)

        if len(numbers) == 2:
            first_num, second_num = numbers[0], numbers[1]
            if prefer_smaller_qty:
                if second_num <= 100 and first_num > second_num:
                    return second_num, first_num
                return first_num, second_num

            first_is_price = (first_num % 1 != 0) and (
                abs((first_num % 1) - 0.99) < 0.01
                or abs((first_num % 1) - 0.95) < 0.01
                or abs((first_num % 1) - 0.50) < 0.01
                or (first_num % 1) < 0.01
            )
            if (first_num > 1000 and second_num < 100) or (
                first_is_price and second_num < 1000
            ):
                return second_num, first_num
            return first_num, second_num

        if len(numbers) == 1 and not prefer_smaller_qty:
            return 1.0, numbers[0]
        return None

    def normalize_line_data(self, lines_data):
        """Normalize regex tuples into (product_name, qty_str, price_str)."""
        normalized = []
        for line_tuple in lines_data:
            if len(line_tuple) < 2:
                continue

            numbers = []
            text_parts = []
            for elem in line_tuple:
                elem_str = str(elem).strip()
                if re.match(r'^[\d\.\,\-]+$', elem_str):
                    num_val = self.clean_number(elem_str)
                    if num_val >= 0:
                        numbers.append(num_val)
                else:
                    text_parts.append(elem_str)

            if not text_parts:
                continue

            product_name = self.clean_product_name(' '.join(text_parts))
            if not self.is_valid_product_line(product_name):
                continue

            qty_price = self._infer_qty_price(numbers)
            if not qty_price:
                continue

            qty, price = qty_price
            if 0 < qty <= 10000 and 0 <= price <= 1000000:
                normalized.append((product_name, str(qty), str(price)))

        return normalized

    def _get_or_create_product(self, product_name):
        """Find an existing product by name or create a consumable."""
        product_model = self.env['product.product']
        return product_model.search(
            [('name', '=', product_name)],
            limit=1,
        ) or product_model.create({'name': product_name, 'type': 'consu'})

    def _collect_valid_lines(self, raw_lines, extractor):
        """Filter raw line tuples into validated (name, qty, price) rows."""
        valid_lines = []
        for raw_line in raw_lines:
            extracted = extractor(raw_line)
            if not extracted:
                continue
            name, qty, price_val = extracted
            if self.is_valid_product_line(name) and qty > 0 and price_val >= 0:
                valid_lines.append((name, qty, price_val))
        return valid_lines

    def _unpack_table_brackets(self, line):
        """Extract (name, qty, price) from a bracketed code table row."""
        if len(line) < 4:
            return None
        name = self.clean_product_name(f"[{line[0].strip()}] {line[1].strip()}")
        return name, self.clean_number(line[2]), self.clean_number(line[3])

    def _unpack_table_simple(self, line):
        """Extract (name, qty, price) from an indexed table row."""
        if len(line) < 4:
            return None
        name = self.clean_product_name(line[1].strip())
        return name, self.clean_number(line[2]), self.clean_number(line[3])

    def _unpack_table_dollar(self, line):
        """Extract (name, qty, price) from a currency-first table row."""
        if len(line) < 3:
            return None
        name = self.clean_product_name(line[0].strip())
        return name, self.clean_number(line[2]), self.clean_number(line[1])

    def _unpack_normalized_line(self, line):
        """Extract (name, qty, price) from an already-normalized tuple."""
        if len(line) < 3:
            return None
        name = self.clean_product_name(str(line[0]).strip())
        return name, self.clean_number(line[1]), self.clean_number(line[2])

    def _extract_code_name_rows(self, matches):
        """Extract product and amount lists from Description tables."""
        extra_lines = matches['name_with_extra_line']
        name_list_one = [f"{code} {name}" for code, name in extra_lines]
        names = [
            item.strip()
            for item in matches['code_name'][0].split('\n')
            if item.strip()
        ]
        if name_list_one and len(name_list_one) > len(names):
            names = name_list_one

        qty_block = (
            matches['quantity_part']
            or matches['quantity_price_amount_pattern']
            or matches['quantity_price_amount_pattern2']
        )
        order_lines = (
            [row.strip() for row in qty_block[0].split('\n') if row.strip()]
            if qty_block
            else []
        )

        products = [
            self._get_or_create_product(self.clean_product_name(name))
            for name in names
        ]
        price = []
        quantity = []
        for row in order_lines:
            tokens = row.split()
            if len(tokens) >= 2:
                quantity.append(self.clean_number(tokens[0]))
                price.append(self.clean_number(tokens[1]))
            else:
                quantity.append(0.0)
                price.append(0.0)
        subtotal = [qty * unit for qty, unit in zip(quantity, price)]
        return products, quantity, price, subtotal

    def _build_rows_from_matches(self, matches):
        """Select highest-priority matched layout and extract line lists."""
        simple_rows = self.normalize_line_data(matches['simple_name_qty_price'])
        name_qty_rows = self.normalize_line_data(matches['name_qty_amount'])
        qty_name_rows = self.normalize_line_data(matches['qty_name_amount'])
        fallback_rows = self.normalize_line_data(matches['fallback'])

        for key, extractor in (
            ('table_brackets', self._unpack_table_brackets),
            ('table_simple', self._unpack_table_simple),
            ('table_dollar', self._unpack_table_dollar),
        ):
            if matches[key]:
                valid = self._collect_valid_lines(matches[key], extractor)
                if valid:
                    return self._materialize_valid_lines(valid)

        if simple_rows or fallback_rows:
            valid = self._collect_valid_lines(simple_rows, self._unpack_normalized_line)
            if len(valid) < 2 and fallback_rows:
                valid.extend(
                    self._collect_valid_lines(
                        fallback_rows,
                        self._unpack_normalized_line,
                    ),
                )
            if valid:
                return self._materialize_valid_lines(valid)

        four_col = (
            matches['name_qty_price_amount2']
            or matches['name_qty_price_amount1']
            or matches['newline_name_qty_price_amount']
        )
        if four_col:
            products = [
                self._get_or_create_product(self.clean_product_name(row[0]))
                for row in four_col
            ]
            quantity = [self.clean_number(row[1]) for row in four_col]
            price = [self.clean_number(row[2]) for row in four_col]
            subtotal = [self.clean_number(row[3]) for row in four_col]
            return products, quantity, price, subtotal

        three_col = name_qty_rows or qty_name_rows or matches['vendor_bill_pattern']
        if three_col:
            products = [
                self._get_or_create_product(self.clean_product_name(row[0]))
                for row in three_col
            ]
            quantity = [self.clean_number(row[1]) for row in three_col]
            price = [self.clean_number(row[2]) for row in three_col]
            subtotal = [qty * unit for qty, unit in zip(quantity, price)]
            return products, quantity, price, subtotal

        price_first = (
            matches['name_price_qty_amount']
            or matches['name_price_qty_amount_with_dollar']
        )
        if price_first:
            products = [
                self._get_or_create_product(self.clean_product_name(row[0]))
                for row in price_first
            ]
            price = [self.clean_number(row[1]) for row in price_first]
            quantity = [self.clean_number(row[2]) for row in price_first]
            subtotal = [self.clean_number(row[3]) for row in price_first]
            return products, quantity, price, subtotal

        if matches['name_amount']:
            rows = matches['name_amount']
            products = [
                self._get_or_create_product(self.clean_product_name(row[0]))
                for row in rows
            ]
            subtotal = [self.clean_number(row[1]) for row in rows]
            quantity = [1.0 for _ in rows]
            return products, quantity, subtotal.copy(), subtotal

        if matches['code_name']:
            return self._extract_code_name_rows(matches)

        return [], [], [], []

    def _materialize_valid_lines(self, valid_lines):
        """Convert (name, qty, price) rows into product/amount lists."""
        if not valid_lines:
            return [], [], [], []
        products = [self._get_or_create_product(line[0]) for line in valid_lines]
        quantity = [line[1] for line in valid_lines]
        price = [line[2] for line in valid_lines]
        subtotal = [line[1] * line[2] for line in valid_lines]
        return products, quantity, price, subtotal

    def _build_move_line_commands(self, products, quantity, price, subtotal):
        """Build Command.create tuples for account.move invoice_line_ids."""
        if products and quantity and price:
            return [
                Command.create({
                    'product_id': product.id,
                    'name': product.name,
                    'price_unit': float(unit_price),
                    'price_subtotal': float(total_amount),
                    'quantity': float(qty),
                    'tax_ids': [Command.set([])],
                })
                for product, unit_price, total_amount, qty in zip(
                    products,
                    price,
                    subtotal,
                    quantity,
                )
            ]

        if products and price:
            return [
                Command.create({
                    'product_id': product.id,
                    'name': product.name,
                    'price_unit': float(unit_price),
                    'price_subtotal': float(total_amount),
                    'quantity': 1.0,
                    'tax_ids': [Command.set([])],
                })
                for product, unit_price, total_amount in zip(
                    products,
                    price,
                    subtotal,
                )
            ]

        if products and subtotal:
            effective_quantities = quantity or [1.0] * len(products)
            return [
                Command.create({
                    'product_id': product.id,
                    'name': product.name,
                    'quantity': float(qty) if qty else 1.0,
                    'price_unit': (
                        float(total_amount) / float(qty)
                        if qty and float(qty) > 0
                        else float(total_amount)
                    ),
                    'price_subtotal': float(total_amount),
                    'tax_ids': [Command.set([])],
                })
                for product, total_amount, qty in zip(
                    products,
                    subtotal,
                    effective_quantities,
                )
            ]

        return []

    def record_lines(self, matches):
        """Convert regex matches into account.move line commands."""
        products, quantity, price, subtotal = self._build_rows_from_matches(matches)

        for line in matches['double_line_name']:
            product_name = self.clean_product_name(f"{line[0]} {line[1]}")
            if not self.is_valid_product_line(product_name):
                continue
            products.append(self._get_or_create_product(product_name))
            subtotal.append(self.clean_number(line[5]))
            price.append(self.clean_number(line[4]))
            quantity.append(self.clean_number(line[3]))

        return self._build_move_line_commands(products, quantity, price, subtotal)

    def _extract_text_patterns(self, text):
        """Apply bill line, date, and reference patterns to OCR text."""
        pattern_specs = {
            'newline_name_qty_price_amount': (
                r'\n([A-Za-z ]+) (\d+) (\d+\.\d{2}) (\d+\.\d{2})'
            ),
            'name_qty_amount': r'\n([A-Za-z ]+) (\d+) (\d+\.\d{2})',
            'qty_name_amount': r'\n(\d+) ([A-Za-z ]+) (\d+\.\d{2})',
            'name_qty_price_amount1': r'\s*([A-Za-z() \d]+) (\d+) (\d+) (\d+)',
            'name_price_qty_amount_with_dollar': (
                r'\n(\$?\w+(?: \w+)*) (\$[\d.]+) (\d+) (\$[\d.]+)'
            ),
            'name_price_qty_amount': (
                r'\n(\$?\w+(?: \w+)*) ([\d.]+) (\d+) ([\d.]+)'
            ),
            'name_amount': r'\n(\$?\w+(?: \w+)*) (\d+\.\d{2})',
            'name_qty_price_amount2': r"([\w\s]+)\s+(\d+)\s+(\d+)\s+\$(\d+)",
            'double_line_name': (
                r'([\w\s]+)\s([\w\s]+)\s*([\w\s]+)\s*(\d+)\s*'
                r'(\$\d+\.\d{2})\s*(\d+\.\d{2})'
            ),
            'code_name': r'Description\n([\s\S]*?)(?=\n\n)',
            'quantity_part': r'Quantity Unit Price Taxes\n([\s\S]*?)(?=\n\n)',
            'vendor_bill_pattern': (
                r'\[[A-Z0-9-]+\] (.+?) (\d+\.\d+) (\d+\.\d+) '
                r'(\d+\.\d+%?) \$ (\d+\.\d+)'
            ),
            'quantity_price_amount_pattern': (
                r'Quantity Unit Price Taxes Amount\n'
                r'((?:\d+\.\d+\s+\d+\.\d+\s+\d+\.\d+% \$\s+\d+\.\d+\n)+)'
            ),
            'quantity_price_amount_pattern2': (
                r'Quantity Unit Price Taxes Amount([\s\S]*?)'
                r'(?:Untaxed Amount|Tax|Total|$)'
            ),
            'name_with_extra_line': r'\[([A-Z0-9-]+)\] (.+)',
            'simple_name_qty_price': (
                r'([A-Za-z][A-Za-z\s\.\-&\(\)]+?)\s+([z\d]+)\s+([\d\)\.\-,]+)'
            ),
            'table_brackets': (
                r'\[([A-Z0-9\-_]+)\]\s+(.+?)\s+'
                r'(?:Units?|Each|Pcs?|pcs?)?\s*'
                r'([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)'
            ),
            'table_simple': (
                r'^(\d+)\s+(.+?)\s+'
                r'(?:Units?|Each|Pcs?|pcs?)?\s*'
                r'([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)'
            ),
            'table_dollar': (
                r'(.+?)\s+\$?([\d,]+\.\d{2})\s+(\d+\.?\d*)\s+\$?([\d,]+\.\d{2})'
            ),
        }
        multiline_keys = {'table_brackets', 'table_simple'}
        matches = {key: [] for key in pattern_specs}
        matches.update({'date_match': None, 'bill_no_match': None, 'fallback': []})

        try:
            for key, pattern in pattern_specs.items():
                flags = re.MULTILINE if key in multiline_keys else 0
                matches[key] = re.findall(pattern, text, flags)
            matches['date_match'] = re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', text)
            matches['bill_no_match'] = re.search(
                r'(?:Bill|Invoice|Receipt)\s*(?:No|#)?[:\s]*([A-Z0-9\-]+)',
                text,
                re.IGNORECASE,
            )
        except re.error as err:
            _logger.warning("Regex matching failed during bill OCR parsing: %s", err)

        primary_keys = (
            'table_brackets',
            'table_simple',
            'table_dollar',
            'simple_name_qty_price',
            'newline_name_qty_price_amount',
            'name_qty_amount',
            'vendor_bill_pattern',
        )
        if not any(matches[key] for key in primary_keys):
            matches['fallback'] = self.parse_lines_intelligently(text)
        return matches

    def _parse_invoice_date(self, date_match):
        """Parse extracted date string or fall back to today."""
        if date_match:
            date_value = date_match.group()
            for fmt in (
                '%d/%m/%Y',
                '%m/%d/%Y',
                '%d-%m-%Y',
                '%m-%d-%Y',
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%d/%m/%y',
                '%m/%d/%y',
            ):
                try:
                    return datetime.strptime(date_value, fmt).date()
                except ValueError:
                    continue
        return fields.Date.context_today(self)

    def create_record(self, text):
        """Parse extracted OCR text and create a draft vendor bill."""
        matches = self._extract_text_patterns(text)
        invoice_date = self._parse_invoice_date(matches['date_match'])
        bill_no_match = matches['bill_no_match']
        bill_no = bill_no_match.group(1) if bill_no_match else ''
        move_line_vals = self.record_lines(matches)

        return self.env['account.move'].create([{
            'move_type': 'in_invoice',
            'ref': bill_no,
            'date': invoice_date,
            'invoice_date': invoice_date,
            'invoice_line_ids': move_line_vals,
        }])

    def parse_lines_intelligently(self, text):
        """Fallback line-by-line parser for unstructured OCR tables."""
        parsed_lines = []
        for raw_line in text.split('\n'):
            cleaned_line = raw_line.strip()
            if len(cleaned_line) < 3:
                continue

            cleaned_line = re.sub(r'^(\d{1,3})\s*[\|\.]\s+', '', cleaned_line)
            cleaned_line = re.sub(r'^\s*[\|]\s*', '', cleaned_line).strip()
            if len(cleaned_line) < 3:
                continue

            tokens = cleaned_line.split()
            if len(tokens) < 2:
                continue

            numbers = []
            text_parts = []
            for token in tokens:
                num_val = self.clean_number(token)
                if num_val > 0 and re.search(r'\d', token):
                    numbers.append(num_val)
                else:
                    text_parts.append(token)

            if len(numbers) < 2 or not text_parts:
                continue

            product_name = self.clean_product_name(' '.join(text_parts))
            if not self.is_valid_product_line(product_name):
                continue

            qty_price = self._infer_qty_price(numbers, prefer_smaller_qty=True)
            if not qty_price:
                continue

            qty, price = qty_price
            if 0 < qty <= 10000 and 0 <= price <= 1000000:
                parsed_lines.append((product_name, str(qty), str(price)))

        return parsed_lines

    def clean_ocr_text(self, text):
        """Correct common OCR character confusions near numbers."""
        cleaned_lines = []
        for raw_line in text.split('\n'):
            fixed = re.sub(r'(\d+\.)i', r'\g<1>1', raw_line)
            fixed = re.sub(r'(\d+\.)l', r'\g<1>1', fixed)
            fixed = re.sub(r'([\$\s])O(\.\d)', r'\g<1>0\g<2>', fixed)
            fixed = re.sub(r'(\d)O(\.\d)', r'\g<1>0\g<2>', fixed)
            fixed = re.sub(r'(\d)O(\d)', r'\g<1>0\g<2>', fixed)
            fixed = re.sub(r'([\s:])l(\d)', r'\g<1>1\g<2>', fixed)
            fixed = re.sub(r'([\s:])I(\d)', r'\g<1>1\g<2>', fixed)
            fixed = re.sub(r'(\d)l(\s|$)', r'\g<1>1\g<2>', fixed)
            fixed = re.sub(r'(\d)I(\s|$)', r'\g<1>1\g<2>', fixed)
            fixed = re.sub(r'(\s)i(\s|$)', r'\g<1>1\g<2>', fixed)
            fixed = re.sub(r'(\s)l(\s|$)', r'\g<1>1\g<2>', fixed)
            cleaned_lines.append(fixed)
        return '\n'.join(cleaned_lines)

    def _preprocess_image_for_ocr(self, img):
        """Convert image to scaled grayscale suitable for Tesseract OCR."""
        rgb_img = img.convert('RGB') if img.mode != 'RGB' else img
        gray_img = rgb_img.convert('L')
        min_width = 2000
        if gray_img.width < min_width:
            scale_factor = min_width / gray_img.width
            new_size = (
                int(gray_img.width * scale_factor),
                int(gray_img.height * scale_factor),
            )
            resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
            gray_img = gray_img.resize(new_size, resample=resample_filter)
        return gray_img

    def _run_tesseract_ocr(self, img, psm_modes):
        """Run Tesseract across fallback PSM modes and return text."""
        processed_img = self._preprocess_image_for_ocr(img)
        text = ''
        for psm in psm_modes:
            try:
                text = pytesseract.image_to_string(
                    processed_img,
                    lang='eng',
                    config=f'--oem 3 --psm {psm}',
                )
            except pytesseract.TesseractNotFoundError as err:
                msg = self.env._("Tesseract is not installed.")
                raise ValidationError(msg) from err
            except pytesseract.TesseractError as err:
                msg = self.env._("Tesseract OCR Error: %(error)s", error=str(err))
                raise ValidationError(msg) from err

            if text and len(text.strip()) >= 10:
                return text
        return text

    def _extract_text_from_pdf(self, binary_data):
        """Render PDF bytes to images and extract OCR text from all pages."""
        try:
            images = convert_from_bytes(binary_data, dpi=400)
        except (
            PDFInfoNotInstalledError,
            PDFPageCountError,
            PDFSyntaxError,
            OSError,
            ValueError,
        ) as err:
            msg = self.env._("Cannot read PDF file: %(error)s", error=str(err))
            raise ValidationError(msg) from err

        if not images:
            raise ValidationError(self.env._("Cannot read PDF file."))

        all_text = []
        for img in images:
            page_text = self._run_tesseract_ocr(img, (6, 4, 11))
            if page_text and len(page_text.strip()) >= 5:
                all_text.append(page_text)

        if not all_text:
            raise ValidationError(self.env._("Unable to extract text from PDF."))
        return '\n'.join(all_text)

    def _extract_text_from_image(self, binary_data):
        """Open image bytes and extract OCR text."""
        try:
            with Image.open(io.BytesIO(binary_data)) as img:
                text = self._run_tesseract_ocr(img, (6, 4, 3, 11))
        except (UnidentifiedImageError, OSError, ValueError) as err:
            msg = self.env._(
                "Cannot identify image data: %(error)s",
                error=str(err),
            )
            raise ValidationError(msg) from err

        if not text or len(text.strip()) < 5:
            raise ValidationError(
                self.env._("Unable to extract text from the document."),
            )
        return text

    def action_add_document(self):
        """Extract OCR text, create a draft bill, and open its form."""
        self.ensure_one()
        file_attachment = self.env['ir.attachment'].search(
            [
                ('res_model', '=', 'digitize.bill'),
                ('res_id', '=', self.id),
                ('res_field', '=', 'bill'),
            ],
            limit=1,
        )
        binary_data = bytes(self.bill) if self.bill else b''
        if not binary_data and file_attachment:
            binary_data = (
                bytes(file_attachment.raw) if file_attachment.raw else b''
            )
        if not binary_data:
            raise ValidationError(self.env._("Please upload a bill document."))

        file_extension = (
            self.file_name.lower().rsplit('.', maxsplit=1)[-1]
            if self.file_name and '.' in self.file_name
            else ''
        )
        if file_extension == 'pdf':
            text = self._extract_text_from_pdf(binary_data)
        else:
            text = self._extract_text_from_image(binary_data)

        cleaned_text = self.clean_ocr_text(text)
        bill_record = self.create_record(cleaned_text)

        if file_attachment and bill_record:
            file_attachment.write({
                'res_model': 'account.move',
                'res_id': bill_record.id,
                'res_field': False,
            })

        return {
            'name': self.env._("Vendor Bill"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': bill_record.id,
            'view_id': self.env.ref('account.view_move_form').id,
            'target': 'current',
        }
