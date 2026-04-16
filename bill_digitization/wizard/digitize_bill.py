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
import io
import pytesseract
import re
from PIL import Image
from pdf2image import convert_from_path
from odoo import Command, fields, models, _
from odoo.exceptions import ValidationError


class DigitizeBill(models.TransientModel):
    _name = "digitize.bill"
    _description = "Digitize Bill"

    bill = fields.Binary(string="Document", required=True,
                         help="Choose a scanned document")
    file_name = fields.Char(string="File Name", help="Name of the file")

    def clean_number(self, value):
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

        value = original_value
        value = value.replace(',', '').replace(' ', '').replace('$', '')
        value = value.replace('Rs', '').replace('₹', '')
        value = value.replace(')', '0').replace('(', '')
        value = value.replace('O', '0').replace('o', '0')
        value = value.replace('l', '1').replace('I', '1')
        value = re.sub(r'\.{2,}', '.', value)

        if '.' not in value and value.count('-') == 1:
            parts = value.split('-')
            if len(parts) == 2 and parts[0].isdigit() and parts[
                1].isdigit() and len(parts[1]) <= 2:
                value = parts[0] + '.' + parts[1]

        value = re.sub(r'[^\d.\-]', '', value)
        parts = value.split('.')
        if len(parts) > 2:
            value = parts[0] + '.' + ''.join(parts[1:])

        value = value.strip('.-')

        if not value or not re.search(r'\d', value):
            return 0.0

        try:
            result = float(value)
            if result > 999999999:
                return 0.0
            return result
        except (ValueError, TypeError):
            numbers = re.findall(r'\d+\.?\d*', value)
            if numbers:
                try:
                    result = float(numbers[0])
                    if result > 999999999:
                        return 0.0
                    return result
                except:
                    return 0.0
            return 0.0

    def clean_product_name(self, product_name):
        name = product_name.strip()

        if '\n' in name:
            name = name.split('\n')[-1].strip()
        if '\r' in name:
            name = name.split('\r')[-1].strip()

        name = re.sub(r'\(.*?\)', '', name)
        name = re.sub(r'\[.*?\]', '', name)
        name = re.sub(r'[_\|]', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        name = name.strip(' ,-')

        return name

    def is_likely_address(self, product_name):
        name_lower = product_name.lower().strip()

        if product_name.count(',') >= 2:
            parts = [p.strip() for p in product_name.split(',')]
            has_short_parts = any(len(part) <= 4 for part in parts if part)
            has_numbers = any(
                re.search(r'\d{4,}', part) for part in parts if part)

            if has_short_parts or has_numbers:
                return True

            is_likely_product = all(
                len(part) > 3 and (part[0].isupper() if part else False)
                for part in parts if part
            )

            if not is_likely_product:
                return True

        address_patterns = [
            r'\b\d{5}(-\d{4})?\b',
            r'\b[A-Z]{2}\s+\d{5}\b',
            r'\bstreet\b', r'\bavenue\b', r'\broad\b', r'\bblvd\b',
            r'\bapt\b', r'\bsuite\b', r'\bunit\b', r'\bfloor\b',
            r'\bpo box\b', r'\bp\.o\.\s*box\b'
        ]

        for pattern in address_patterns:
            if re.search(pattern, name_lower):
                return True

        return False

    def is_valid_product_line(self, product_name):
        if not product_name or len(product_name) < 3:
            return False

        name_lower = product_name.lower().strip()

        skip_patterns = [
            r'^\s*invoice\b', r'^\s*bill\b', r'^\s*receipt\b', r'^\s*total\b',
            r'^\s*subtotal\b', r'^\s*tax\b', r'^\s*amount\b',
            r'^\s*description\b',
            r'^\s*qty\b', r'^\s*quantity\b', r'^\s*price\b', r'^\s*unit\b',
            r'^\s*item\b', r'^\s*product\b', r'^\s*date\b', r'^\s*customer\b',
            r'^\s*vendor\b', r'^\s*phone\b', r'^\s*mobile\b', r'^\s*email\b',
            r'^\s*website\b', r'^\s*payment\b', r'^\s*terms\b',
            r'^\s*account\b',
            r'^\s*bank\b', r'^\s*page\b', r'^\s*signature\b', r'^\s*discount\b',
            r'^\s*grand\b', r'^\s*comments\b', r'^\s*salesperson\b',
            r'^\s*reference\b', r'^\s*balance\b', r'^\s*due\b', r'^\s*address\b'
        ]

        for pattern in skip_patterns:
            if re.search(pattern, name_lower):
                return False

        if any(phrase in name_lower for phrase in
               ['ship to', 'bill to', 'sold to', 'thank you', 'p.o. number',
                'due date', 'due after', 'payment reference']):
            return False

        if self.is_likely_address(product_name):
            return False

        words = product_name.split()
        if len(words) >= 3 and len(set(words)) / len(words) < 0.6:
            return False

        if len(re.findall(r'[A-Za-z0-9]', product_name)) < len(
                product_name) * 0.5:
            return False

        if len(product_name) > 100:
            return False

        return True

    def normalize_line_data(self, lines_data):
        normalized = []

        for idx, line_tuple in enumerate(lines_data):
            if len(line_tuple) < 2:
                continue

            elements = list(line_tuple)
            numbers = []
            text_parts = []

            for elem in elements:
                elem_str = str(elem).strip()
                if re.match(r'^[\d\.\,\-]+$', elem_str):
                    try:
                        num_val = self.clean_number(elem_str)
                        if num_val >= 0:
                            numbers.append(num_val)
                    except:
                        text_parts.append(elem_str)
                else:
                    text_parts.append(elem_str)

            if len(text_parts) < 1:
                continue

            product_name = ' '.join(text_parts)
            product_name = self.clean_product_name(product_name)

            if not self.is_valid_product_line(product_name):
                continue

            if len(numbers) >= 3:
                expected_total = numbers[0] * numbers[1]
                tolerance = max(0.1, expected_total * 0.01)

                if abs(numbers[2] - expected_total) < tolerance:
                    qty = numbers[0]
                    price = numbers[1]
                elif abs(numbers[2] - (numbers[1] * numbers[0])) < tolerance:
                    qty = numbers[1]
                    price = numbers[0]
                else:
                    if numbers[0] <= 100 and numbers[0] % 1 == 0 and numbers[
                        1] % 1 != 0:
                        qty = numbers[0]
                        price = numbers[1]
                    elif numbers[1] <= 100 and numbers[1] % 1 == 0 and numbers[
                        0] % 1 != 0:
                        qty = numbers[1]
                        price = numbers[0]
                    elif numbers[0] <= 100 and numbers[1] > numbers[0] and \
                            numbers[1] < 100000:
                        qty = numbers[0]
                        price = numbers[1]
                    else:
                        qty = numbers[0]
                        price = numbers[1]

            elif len(numbers) == 2:
                first_num = numbers[0]
                second_num = numbers[1]

                first_is_price = (first_num % 1 != 0) and (
                        abs((first_num % 1) - 0.99) < 0.01 or
                        abs((first_num % 1) - 0.95) < 0.01 or
                        abs((first_num % 1) - 0.50) < 0.01 or
                        (first_num % 1) < 0.01
                )

                if first_num > 1000 and second_num < 100:
                    qty = second_num
                    price = first_num
                elif first_is_price and second_num < 1000:
                    qty = second_num
                    price = first_num
                else:
                    qty = first_num
                    price = second_num

            elif len(numbers) == 1:
                qty = 1.0
                price = numbers[0]
            else:
                continue

            if qty > 0 and qty <= 10000 and price >= 0 and price <= 1000000:
                normalized.append((product_name, str(qty), str(price)))

        return normalized

    def record_lines(self, product_lines_newline_name_qty_price_amount,
                     product_lines_name_qty_amount,
                     product_lines_qty_name_amount,
                     product_lines_name_qty_price_amount1,
                     product_lines_name_price_qty_amount_with_dollar,
                     product_lines_name_price_qty_amount,
                     product_lines_name_amount,
                     product_lines_name_qty_price_amount2,
                     product_lines_double_line_name,
                     product_lines_code_name,
                     product_lines_quantity_part,
                     product_lines_vendor_bill_pattern,
                     product_lines_quantity_price_amount_pattern,
                     product_lines_quantity_price_amount_pattern2,
                     product_line_name_with_extra_line,
                     product_lines_simple_name_qty_price,
                     product_lines_table_brackets,
                     product_lines_table_simple,
                     product_lines_table_dollar,
                     product_lines_fallback):
        products = []
        price = []
        subtotal = []
        quantity = []

        if product_lines_simple_name_qty_price:
            product_lines_simple_name_qty_price = self.normalize_line_data(
                product_lines_simple_name_qty_price)
        if product_lines_name_qty_amount:
            product_lines_name_qty_amount = self.normalize_line_data(
                product_lines_name_qty_amount)
        if product_lines_qty_name_amount:
            product_lines_qty_name_amount = self.normalize_line_data(
                product_lines_qty_name_amount)
        if product_lines_fallback:
            product_lines_fallback = self.normalize_line_data(
                product_lines_fallback)

        if product_lines_table_brackets:
            valid_lines = []
            for line in product_lines_table_brackets:
                try:
                    code = line[0].strip()
                    name = f"[{code}] {line[1].strip()}"
                    name = self.clean_product_name(name)
                    qty = self.clean_number(line[2])
                    price_val = self.clean_number(line[3])

                    if self.is_valid_product_line(
                            name) and qty > 0 and price_val >= 0:
                        valid_lines.append((name, qty, price_val))
                except Exception:
                    continue

            if valid_lines:
                products = [
                    self.env['product.product'].search([('name', '=', line[0])],
                                                       limit=1) or
                    self.env['product.product'].create(
                        {'name': line[0], 'type': 'consu'})
                    for line in valid_lines
                ]
                quantity = [line[1] for line in valid_lines]
                price = [line[2] for line in valid_lines]
                subtotal = [line[1] * line[2] for line in valid_lines]

        elif product_lines_table_simple:
            valid_lines = []
            for line in product_lines_table_simple:
                try:
                    name = self.clean_product_name(line[1].strip())
                    qty = self.clean_number(line[2])
                    price_val = self.clean_number(line[3])

                    if self.is_valid_product_line(
                            name) and qty > 0 and price_val >= 0:
                        valid_lines.append((name, qty, price_val))
                except Exception:
                    continue

            if valid_lines:
                products = [
                    self.env['product.product'].search([('name', '=', line[0])],
                                                       limit=1) or
                    self.env['product.product'].create(
                        {'name': line[0], 'type': 'consu'})
                    for line in valid_lines
                ]
                quantity = [line[1] for line in valid_lines]
                price = [line[2] for line in valid_lines]
                subtotal = [line[1] * line[2] for line in valid_lines]

        elif product_lines_table_dollar:
            valid_lines = []
            for line in product_lines_table_dollar:
                try:
                    name = self.clean_product_name(line[0].strip())
                    price_val = self.clean_number(line[1])
                    qty = self.clean_number(line[2])

                    if self.is_valid_product_line(
                            name) and qty > 0 and price_val >= 0:
                        valid_lines.append((name, qty, price_val))
                except Exception:
                    continue

            if valid_lines:
                products = [
                    self.env['product.product'].search([('name', '=', line[0])],
                                                       limit=1) or
                    self.env['product.product'].create(
                        {'name': line[0], 'type': 'consu'})
                    for line in valid_lines
                ]
                quantity = [line[1] for line in valid_lines]
                price = [line[2] for line in valid_lines]
                subtotal = [line[1] * line[2] for line in valid_lines]

        elif product_lines_simple_name_qty_price or product_lines_fallback:
            valid_lines = []

            if product_lines_simple_name_qty_price:
                for line in product_lines_simple_name_qty_price:
                    try:
                        name = self.clean_product_name(line[0].strip())
                        qty = self.clean_number(line[1])
                        price_val = self.clean_number(line[2])

                        if self.is_valid_product_line(
                                name) and qty > 0 and price_val >= 0:
                            valid_lines.append((name, qty, price_val))
                    except Exception:
                        continue

            if len(valid_lines) < 2 and product_lines_fallback:
                for line in product_lines_fallback:
                    try:
                        name = self.clean_product_name(line[0].strip())
                        qty = self.clean_number(line[1])
                        price_val = self.clean_number(line[2])

                        if self.is_valid_product_line(
                                name) and qty > 0 and price_val >= 0:
                            valid_lines.append((name, qty, price_val))
                    except Exception:
                        continue

            if valid_lines:
                products = [
                    self.env['product.product'].search([('name', '=', line[0])],
                                                       limit=1) or
                    self.env['product.product'].create(
                        {'name': line[0], 'type': 'consu'})
                    for line in valid_lines
                ]
                quantity = [line[1] for line in valid_lines]
                price = [line[2] for line in valid_lines]
                subtotal = [line[1] * line[2] for line in valid_lines]

        elif (product_lines_newline_name_qty_price_amount or
              product_lines_name_qty_price_amount1 or
              product_lines_name_qty_price_amount2):
            if product_lines_name_qty_price_amount1:
                product_lines_newline_name_qty_price_amount = product_lines_name_qty_price_amount1
            if product_lines_name_qty_price_amount2:
                product_lines_newline_name_qty_price_amount = product_lines_name_qty_price_amount2

            products = [
                self.env['product.product'].search(
                    [('name', '=', self.clean_product_name(line[0]))],
                    limit=1) or
                self.env['product.product'].create(
                    {'name': self.clean_product_name(line[0])})
                for line in product_lines_newline_name_qty_price_amount]
            quantity = [self.clean_number(line[1]) for line in
                        product_lines_newline_name_qty_price_amount]
            price = [self.clean_number(line[2]) for line in
                     product_lines_newline_name_qty_price_amount]
            subtotal = [self.clean_number(line[3]) for line in
                        product_lines_newline_name_qty_price_amount]

        elif product_lines_name_qty_amount:
            products = [
                self.env['product.product'].search(
                    [('name', '=', self.clean_product_name(line[0]))],
                    limit=1) or
                self.env['product.product'].create(
                    {'name': self.clean_product_name(line[0])})
                for line in product_lines_name_qty_amount]
            quantity = [self.clean_number(line[1]) for line in
                        product_lines_name_qty_amount]
            price = [self.clean_number(line[2]) for line in
                     product_lines_name_qty_amount]
            subtotal = [quantity[i] * price[i] for i in range(len(quantity))]

        elif product_lines_qty_name_amount:
            products = [
                self.env['product.product'].search(
                    [('name', '=', self.clean_product_name(line[0]))],
                    limit=1) or
                self.env['product.product'].create(
                    {'name': self.clean_product_name(line[0])})
                for line in product_lines_qty_name_amount]
            quantity = [self.clean_number(line[1]) for line in
                        product_lines_qty_name_amount]
            price = [self.clean_number(line[2]) for line in
                     product_lines_qty_name_amount]
            subtotal = [quantity[i] * price[i] for i in range(len(quantity))]

        elif (
                product_lines_name_price_qty_amount_with_dollar or product_lines_name_price_qty_amount):
            if product_lines_name_price_qty_amount:
                product_lines_name_price_qty_amount_with_dollar = product_lines_name_price_qty_amount

            products = [
                self.env['product.product'].search(
                    [('name', '=', self.clean_product_name(line[0]))],
                    limit=1) or
                self.env['product.product'].create(
                    {'name': self.clean_product_name(line[0])})
                for line in product_lines_name_price_qty_amount_with_dollar]
            price = [self.clean_number(line[1]) for line in
                     product_lines_name_price_qty_amount_with_dollar]
            quantity = [self.clean_number(line[2]) for line in
                        product_lines_name_price_qty_amount_with_dollar]
            subtotal = [self.clean_number(line[3]) for line in
                        product_lines_name_price_qty_amount_with_dollar]

        elif product_lines_name_amount:
            products = [
                self.env['product.product'].search(
                    [('name', '=', self.clean_product_name(line[0]))],
                    limit=1) or
                self.env['product.product'].create(
                    {'name': self.clean_product_name(line[0])})
                for line in product_lines_name_amount]
            subtotal = [self.clean_number(line[1]) for line in
                        product_lines_name_amount]
            quantity = [1.0 for _ in product_lines_name_amount]
            price = subtotal.copy()

        elif product_lines_code_name:
            name_list_one = []
            if product_line_name_with_extra_line:
                for code, name in product_line_name_with_extra_line:
                    name_list_one.append(f"{code} {name}")
            names = [item.strip() for item in
                     product_lines_code_name[0].split('\n') if item.strip()]
            if name_list_one and len(name_list_one) > len(names):
                names = name_list_one

            if product_lines_quantity_part:
                order_lines = [line.strip() for line in
                               product_lines_quantity_part[0].split('\n') if
                               line.strip()]
            elif product_lines_quantity_price_amount_pattern:
                order_lines = [line.strip() for line in
                               product_lines_quantity_price_amount_pattern[
                                   0].split('\n') if line.strip()]
            elif product_lines_quantity_price_amount_pattern2:
                order_lines = [line.strip() for line in
                               product_lines_quantity_price_amount_pattern2[
                                   0].split('\n') if line.strip()]
            else:
                order_lines = []

            products = [
                self.env['product.product'].search(
                    [('name', '=', self.clean_product_name(name))], limit=1) or
                self.env['product.product'].create(
                    {'name': self.clean_product_name(name)})
                for name in names]
            price = [self.clean_number(line.split()[1]) if line else 0 for line
                     in order_lines]
            quantity = [self.clean_number(line.split()[0]) if line else 0 for
                        line in order_lines]
            subtotal = [quantity[i] * price[i] for i in range(len(quantity))]

        elif product_lines_vendor_bill_pattern:
            products = [
                self.env['product.product'].search(
                    [('name', '=', self.clean_product_name(item[0]))],
                    limit=1) or
                self.env['product.product'].create(
                    {'name': self.clean_product_name(item[0])})
                for item in product_lines_vendor_bill_pattern]
            quantity = [self.clean_number(item[1]) for item in
                        product_lines_vendor_bill_pattern]
            price = [self.clean_number(item[2]) for item in
                     product_lines_vendor_bill_pattern]
            subtotal = [quantity[i] * price[i] for i in range(len(quantity))]

        if product_lines_double_line_name:
            for line in product_lines_double_line_name:
                product_name = self.clean_product_name(line[0] + ' ' + line[1])
                if not self.is_valid_product_line(product_name):
                    continue
                product = self.env['product.product'].search(
                    [('name', '=', product_name)], limit=1)
                if not product:
                    product = self.env['product.product'].create(
                        {'name': product_name})
                products.append(product)
                subtotal.append(self.clean_number(line[5]))
                price.append(self.clean_number(line[4]))
                quantity.append(self.clean_number(line[3]))

        if products and quantity and price:
            move_line_vals = [
                (0, 0, {
                    'product_id': product.id,
                    'name': product.name,
                    'price_unit': float(price_amount),
                    'price_subtotal': float(total_amount),
                    'quantity': float(qty),
                    'tax_ids': [Command.set([])],
                })
                for product, price_amount, total_amount, qty in
                zip(products, price, subtotal, quantity)
            ]
        elif products and price:
            move_line_vals = [
                (0, 0, {
                    'product_id': product.id,
                    'name': product.name,
                    'price_unit': float(price_amount),
                    'price_subtotal': float(total_amount),
                    'quantity': 1.0,
                    'tax_ids': [Command.set([])],
                })
                for product, price_amount, total_amount in
                zip(products, price, subtotal)
            ]
        elif products and subtotal:
            move_line_vals = [
                (0, 0, {
                    'product_id': product.id,
                    'name': product.name,
                    'quantity': float(qty) if qty else 1.0,
                    'price_unit': float(total_amount) / float(
                        qty) if qty and float(qty) > 0 else float(total_amount),
                    'price_subtotal': float(total_amount),
                    'tax_ids': [Command.set([])],
                })
                for product, total_amount, qty in zip(products, subtotal,
                                                      quantity if quantity else [1.0] * len(
                                                          products))
            ]
        else:
            move_line_vals = []

        return move_line_vals

    def create_record(self, text):
        newline_name_qty_price_amount = r'\n([A-Za-z ]+) (\d+) (\d+\.\d{2}) (\d+\.\d{2})'
        name_qty_amount = r'\n([A-Za-z ]+) (\d+) (\d+\.\d{2})'
        qty_name_amount = r'\n(\d+) ([A-Za-z ]+) (\d+\.\d{2})'
        name_qty_price_amount1 = r'\s*([A-Za-z() \d]+) (\d+) (\d+) (\d+)'
        name_price_qty_amount_with_dollar = r'\n(\$?\w+(?: \w+)*) (\$[\d.]+) (\d+) (\$[\d.]+)'
        name_price_qty_amount = r'\n(\$?\w+(?: \w+)*) (\[\d.]+) (\d+) (\[\d.]+)'
        name_amount = r'\n(\$?\w+(?: \w+)*) (\d+\.\d{2})'
        name_qty_price_amount2 = r"([\w\s]+)\s+(\d+)\s+(\d+)\s+\$(\d+)"
        double_line_name = r'([\w\s]+)\s([\w\s]+)\s*([\w\s]+)\s*(\d+)\s*(\$\d+\.\d{2})\s*(\d+\.\d{2})'
        code_name = r'Description\n([\s\S]*?)(?=\n\n)'
        quantity_price_pattern = r'Quantity Unit Price Taxes\n([\s\S]*?)(?=\n\n)'
        vendor_bill_pattern = r'\[[A-Z0-9-]+\] (.+?) (\d+\.\d+) (\d+\.\d+) (\d+\.\d+%?) \$ (\d+\.\d+)'
        quantity_price_amount_pattern = r'Quantity Unit Price Taxes Amount\n((?:\d+\.\d+\s+\d+\.\d+\s+\d+\.\d+% \$\s+\d+\.\d+\n)+)'
        quantity_price_amount_pattern2 = r'Quantity Unit Price Taxes Amount([\s\S]*?)(?:Untaxed Amount|Tax|Total|$)'
        name_with_extra_line = r'\[([A-Z0-9-]+)\] (.+)'
        simple_name_qty_price = r'([A-Za-z][A-Za-z\s\.\-&\(\)]+?)\s+([z\d]+)\s+([\d\)\.\-,]+)'
        table_with_brackets = r'\[([A-Z0-9\-_]+)\]\s+(.+?)\s+(?:Units?|Each|Pcs?|pcs?)?\s*([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)'
        table_simple = r'^(\d+)\s+(.+?)\s+(?:Units?|Each|Pcs?|pcs?)?\s*([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)'
        table_with_dollar = r'(.+?)\s+\$?([\d,]+\.\d{2})\s+(\d+\.?\d*)\s+\$?([\d,]+\.\d{2})'
        date_pattern = r'\d{1,2}/\d{1,2}/\d{2,4}'
        bill_no_pattern = r'(?:Bill|Invoice|Receipt)\s*(?:No|#)?[:\s]*([A-Z0-9\-]+)'

        try:
            product_lines_newline_name_qty_price_amount = re.findall(
                newline_name_qty_price_amount, text)
            product_lines_name_qty_amount = re.findall(name_qty_amount, text)
            product_lines_simple_name_qty_price = re.findall(
                simple_name_qty_price, text)
            product_lines_qty_name_amount = re.findall(qty_name_amount, text)
            product_lines_name_qty_price_amount1 = re.findall(
                name_qty_price_amount1, text)
            product_lines_name_price_qty_amount_with_dollar = re.findall(
                name_price_qty_amount_with_dollar, text)
            product_lines_name_price_qty_amount = re.findall(
                name_price_qty_amount, text)
            product_lines_name_amount = re.findall(name_amount, text)
            product_lines_name_qty_price_amount2 = re.findall(
                name_qty_price_amount2, text)
            product_lines_double_line_name = re.findall(double_line_name, text)
            date_match = re.search(date_pattern, text)
            bill_no_match = re.search(bill_no_pattern, text, re.IGNORECASE)
            product_lines_code_name = re.findall(code_name, text)
            product_lines_quantity_part = re.findall(quantity_price_pattern,
                                                     text)
            product_lines_vendor_bill_pattern = re.findall(vendor_bill_pattern,
                                                           text)
            product_lines_quantity_price_amount_pattern = re.findall(
                quantity_price_amount_pattern, text)
            product_lines_quantity_price_amount_pattern2 = re.findall(
                quantity_price_amount_pattern2, text)
            product_line_name_with_extra_line = re.findall(name_with_extra_line,
                                                           text)
            product_lines_table_brackets = re.findall(table_with_brackets, text,
                                                      re.MULTILINE)
            product_lines_table_simple = re.findall(table_simple, text,
                                                    re.MULTILINE)
            product_lines_table_dollar = re.findall(table_with_dollar, text)
        except Exception:
            product_lines_newline_name_qty_price_amount = []
            product_lines_name_qty_amount = []
            product_lines_simple_name_qty_price = []
            product_lines_qty_name_amount = []
            product_lines_name_qty_price_amount1 = []
            product_lines_name_price_qty_amount_with_dollar = []
            product_lines_name_price_qty_amount = []
            product_lines_name_amount = []
            product_lines_name_qty_price_amount2 = []
            product_lines_double_line_name = []
            product_lines_code_name = []
            product_lines_quantity_part = []
            product_lines_vendor_bill_pattern = []
            product_lines_quantity_price_amount_pattern = []
            product_lines_quantity_price_amount_pattern2 = []
            product_line_name_with_extra_line = []
            product_lines_table_brackets = []
            product_lines_table_simple = []
            product_lines_table_dollar = []
            date_match = None
            bill_no_match = None

        product_lines_fallback = []
        if not any([
            product_lines_table_brackets,
            product_lines_table_simple,
            product_lines_table_dollar,
            product_lines_simple_name_qty_price,
            product_lines_newline_name_qty_price_amount,
            product_lines_name_qty_amount,
            product_lines_vendor_bill_pattern
        ]):
            product_lines_fallback = self.parse_lines_intelligently(text)

        date_object = ''
        if date_match:
            date_value = date_match.group()
            try:
                for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y',
                            '%Y-%m-%d', '%Y/%m/%d', '%d/%m/%y', '%m/%d/%y']:
                    try:
                        date_object = fields.datetime.strptime(date_value, fmt)
                        break
                    except:
                        continue
            except:
                pass
            date = date_object.strftime(
                '%Y-%m-%d') if date_object else fields.Date.today()
        else:
            date = fields.Date.today()

        bill_no = bill_no_match.group(1) if bill_no_match else ''

        move_line_vals = self.record_lines(
            product_lines_newline_name_qty_price_amount,
            product_lines_name_qty_amount,
            product_lines_qty_name_amount,
            product_lines_name_qty_price_amount1,
            product_lines_name_price_qty_amount_with_dollar,
            product_lines_name_price_qty_amount,
            product_lines_name_amount,
            product_lines_name_qty_price_amount2,
            product_lines_double_line_name,
            product_lines_code_name,
            product_lines_quantity_part,
            product_lines_vendor_bill_pattern,
            product_lines_quantity_price_amount_pattern,
            product_lines_quantity_price_amount_pattern2,
            product_line_name_with_extra_line,
            product_lines_simple_name_qty_price,
            product_lines_table_brackets,
            product_lines_table_simple,
            product_lines_table_dollar,
            product_lines_fallback
        )

        bill_record = self.env['account.move'].create([{
            'move_type': 'in_invoice',
            'ref': bill_no,
            'date': date,
            'invoice_date': date,
            'invoice_line_ids': move_line_vals,
        }])

        return bill_record

    def parse_lines_intelligently(self, text):
        lines = text.split('\n')
        parsed_lines = []

        for idx, line in enumerate(lines):
            original_line = line
            line = line.strip()

            if len(line) < 3:
                continue

            line = re.sub(r'^(\d{1,3})\s*[\|\.]\s+', '', line)
            line = re.sub(r'^\s*[\|]\s*', '', line)
            line = line.strip()

            if len(line) < 3:
                continue

            tokens = line.split()
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

            if len(numbers) < 2 or len(text_parts) < 1:
                continue

            product_name = ' '.join(text_parts)
            product_name = self.clean_product_name(product_name)

            if not self.is_valid_product_line(product_name):
                continue

            if len(numbers) >= 3:
                qty = numbers[0]
                unit_price = numbers[1]
                total = numbers[2]

                expected_total = qty * unit_price
                tolerance = max(0.1, expected_total * 0.01)

                if abs(total - expected_total) < tolerance:
                    price = unit_price
                else:
                    qty_alt = numbers[1]
                    price_alt = numbers[0]
                    expected_total_alt = qty_alt * price_alt

                    if abs(total - expected_total_alt) < tolerance:
                        qty = qty_alt
                        price = price_alt
                    else:
                        if numbers[0] <= 100 and numbers[0] % 1 == 0 and \
                                numbers[1] % 1 != 0:
                            qty = numbers[0]
                            price = numbers[1]
                        elif numbers[1] <= 100 and numbers[1] % 1 == 0 and \
                                numbers[0] % 1 != 0:
                            qty = numbers[1]
                            price = numbers[0]
                        elif numbers[0] <= 100 and numbers[1] > numbers[0] and \
                                numbers[1] < 100000:
                            qty = numbers[0]
                            price = numbers[1]
                        else:
                            qty = numbers[0]
                            price = numbers[1]

            elif len(numbers) == 2:
                if numbers[0] <= 100 and numbers[1] > numbers[0]:
                    qty = numbers[0]
                    price = numbers[1]
                elif numbers[1] <= 100 and numbers[0] > numbers[1]:
                    qty = numbers[1]
                    price = numbers[0]
                else:
                    qty = numbers[0]
                    price = numbers[1]
            else:
                continue

            if qty > 0 and qty <= 10000 and price >= 0 and price <= 1000000:
                parsed_lines.append((product_name, str(qty), str(price)))

        return parsed_lines

    def clean_ocr_text(self, text):
        cleaned_lines = []
        for line in text.split('\n'):
            line = re.sub(r'(\d+\.)i', r'\g<1>1', line)
            line = re.sub(r'(\d+\.)l', r'\g<1>1', line)
            line = re.sub(r'([\$\s])O(\.\d)', r'\g<1>0\g<2>', line)
            line = re.sub(r'(\d)O(\.\d)', r'\g<1>0\g<2>', line)
            line = re.sub(r'(\d)O(\d)', r'\g<1>0\g<2>', line)
            line = re.sub(r'([\s:])l(\d)', r'\g<1>1\g<2>', line)
            line = re.sub(r'([\s:])I(\d)', r'\g<1>1\g<2>', line)
            line = re.sub(r'(\d)l(\s|$)', r'\g<1>1\g<2>', line)
            line = re.sub(r'(\d)I(\s|$)', r'\g<1>1\g<2>', line)
            line = re.sub(r'(\s)i(\s|$)', r'\g<1>1\g<2>', line)
            line = re.sub(r'(\s)l(\s|$)', r'\g<1>1\g<2>', line)
            cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)

    def action_add_document(self):
        try:
            file_attachment = self.env["ir.attachment"].search(
                ['|', ('res_field', '!=', False), ('res_field', '=', False),
                 ('res_id', '=', self.id),
                 ('res_model', '=', 'digitize.bill')],
                limit=1)
            file_path = file_attachment._full_path(file_attachment.store_fname)
            file_extension = self.file_name.lower().split('.')[
                -1] if self.file_name else ''

            if file_extension == 'pdf':
                images = convert_from_path(file_path, dpi=400)
                if not images:
                    raise ValidationError(_("Cannot read PDF file"))

                all_text = []
                for img in images:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img = img.convert('L')

                    min_width = 2000
                    if img.width < min_width:
                        scale_factor = min_width / img.width
                        new_size = (int(img.width * scale_factor),
                                    int(img.height * scale_factor))
                        img = img.resize(new_size, resample=Image.LANCZOS)

                    try:
                        custom_config = r'--oem 3 --psm 6'
                        page_text = pytesseract.image_to_string(img, lang='eng',
                                                                config=custom_config)

                        if not page_text or len(page_text.strip()) < 10:
                            custom_config = r'--oem 3 --psm 4'
                            page_text = pytesseract.image_to_string(img,
                                                                    lang='eng',
                                                                    config=custom_config)

                        if not page_text or len(page_text.strip()) < 10:
                            custom_config = r'--oem 3 --psm 11'
                            page_text = pytesseract.image_to_string(img,
                                                                    lang='eng',
                                                                    config=custom_config)

                        if page_text and len(page_text.strip()) >= 5:
                            all_text.append(page_text)
                    except:
                        continue

                if not all_text:
                    raise ValidationError(_("Unable to extract text from PDF"))

                text = '\n'.join(all_text)
            else:
                with open(file_path, mode='rb') as file:
                    binary_data = file.read()
                img = Image.open(io.BytesIO(binary_data))

                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img = img.convert('L')

                min_width = 2000
                if img.width < min_width:
                    scale_factor = min_width / img.width
                    new_size = (int(img.width * scale_factor),
                                int(img.height * scale_factor))
                    img = img.resize(new_size, resample=Image.LANCZOS)

                try:
                    custom_config = r'--oem 3 --psm 6'
                    text = pytesseract.image_to_string(img, lang='eng',
                                                       config=custom_config)

                    if not text or len(text.strip()) < 10:
                        custom_config = r'--oem 3 --psm 4'
                        text = pytesseract.image_to_string(img, lang='eng',
                                                           config=custom_config)

                    if not text or len(text.strip()) < 10:
                        custom_config = r'--oem 3 --psm 3'
                        text = pytesseract.image_to_string(img, lang='eng',
                                                           config=custom_config)

                    if not text or len(text.strip()) < 10:
                        custom_config = r'--oem 3 --psm 11'
                        text = pytesseract.image_to_string(img, lang='eng',
                                                           config=custom_config)

                    if not text or len(text.strip()) < 5:
                        raise ValidationError(
                            _("Unable to extract text from the document."))
                except pytesseract.TesseractError as te:
                    raise ValidationError(
                        _("Tesseract OCR Error: %s") % str(te))
                except pytesseract.TesseractNotFoundError:
                    raise ValidationError(_("Tesseract is not installed."))

        except Exception as e:
            raise ValidationError(_("Cannot identify data: %s") % str(e))

        text = self.clean_ocr_text(text)
        bill_record = self.create_record(text)

        if file_attachment and bill_record:
            file_attachment.write({
                'res_model': 'account.move',
                'res_id': bill_record.id,
                'res_field': False,
            })

        return {
            'name': "Invoice",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': bill_record.id,
            'view_id': self.env.ref('account.view_move_form').id,
            'target': 'current',
        }
