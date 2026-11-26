# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil Ashok (odoo@cybrosys.com)
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
###############################################################################
"""Import bank statement files (CAMT.052/.053/.054, MT940, CSV, XLSX, OFX,
QIF) into bank, cash and credit card journals.

Each reader returns a list of statements (see ``bank_statement_formats``);
``_create_statements`` checks the account and currency against the journal
(or finds the journal from the account number), skips the transactions
already imported, creates one statement per statement of the file with the
original file attached, and sets the balances. CSV / XLSX files are read
with the journal's saved format, else by their column titles; when neither
works the wizard asks which column holds what and can save the answer as
the journal's format.
"""
import csv
import io
import os
import re
from collections import Counter
from datetime import date, datetime

import openpyxl
from ofxparse import OfxParser
from qifparse.parser import QifParser

from odoo import Command, _, api, fields, models
from odoo.addons.base.models.res_partner_bank import sanitize_account_number
from odoo.exceptions import UserError

from ..models.kit_statement_import_map import COLUMN_FIELDS
from . import bank_statement_formats as formats

# Accepted column titles (lower case) for CSV and XLSX files without a
# saved format.
HEADERS = {
    'date': ['date', 'transaction date', 'value date', 'booking date',
             'line_ids/date'],
    'amount': ['amount', 'value', 'line_ids/amount'],
    'debit': ['debit', 'withdrawal', 'money out'],
    'credit': ['credit', 'deposit', 'money in'],
    'label': ['label', 'description', 'name', 'memo', 'narration',
              'details', 'payment_ref', 'line_ids/payment_ref'],
    'partner': ['partner', 'partner_id/name', 'partner_id', 'contact',
                'payee', 'customer', 'supplier', 'line_ids/partner_id'],
    'partner_account': ['partner account', 'iban', 'counterparty account',
                        'account number'],
    'reference': ['reference', 'ref'],
    'unique_id': ['transaction id', 'id'],
    'balance': ['balance', 'running balance', 'ending balance',
                'end balance', 'balance_end_real'],
    'balance_start': ['starting balance', 'start balance',
                      'opening balance', 'balance_start'],
}
AUTO_DATE_FORMATS = ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y',
                     '%Y/%m/%d', '%d.%m.%Y')
TABLE_EXTENSIONS = ('.csv', '.xlsx')
FILE_TYPES = "CAMT (XML), MT940, CSV, XLSX, OFX or QIF"


# journal types that receive bank statements
STATEMENT_JOURNAL_TYPES = ('bank', 'cash', 'credit')

class ImportBankStatement(models.TransientModel):
    """Upload one or more statement files."""
    _name = "import.bank.statement"
    _inherit = ['kit.statement.import.options']
    _description = "Import Bank Statement"
    _rec_name = "file_name"

    attachment = fields.Binary(string="File", help="Choose the file to import")
    file_name = fields.Char(string="File Name", help="Name of the file")
    attachment_ids = fields.Many2many(
        'ir.attachment', 'kit_import_bank_statement_attachment_rel',
        'wizard_id', 'attachment_id', string="Files",
        help="One or more statement files; each statement of each file "
             "becomes its own bank statement.")
    journal_id = fields.Many2one(
        'account.journal', string="Journal",
        default=lambda self: self._default_journal(),
        domain="[('company_id', 'in', allowed_company_ids),"
               " ('type', 'in', ('bank', 'cash', 'credit'))]",
        help="Bank, cash or credit card journal that receives the statement. "
             "Leave it empty for CAMT, MT940 and OFX files: the journal is "
             "found from the account number in the file.")
    state = fields.Selection([('upload', 'Upload'), ('columns', 'Columns')],
                             default='upload', required=True)
    map_id = fields.Many2one(
        'kit.statement.import.map', string="Saved Format",
        domain="[('journal_id', '=', journal_id)]",
        help="The journal's saved CSV / XLSX format.")
    column_ids = fields.One2many('import.bank.statement.column', 'wizard_id',
                                 string="Columns")
    save_map = fields.Boolean(string="Save as Format for This Journal",
                              default=True)
    map_name = fields.Char(string="Format Name")

    @api.model
    def _default_journal(self):
        """The journal of the dashboard card, else the only bank journal of
        the current company."""
        journals = self.env['account.journal'].search([
            ('type', '=', 'bank'),
            *self.env['account.journal']._check_company_domain(
                self.env.company),
        ], limit=2)
        return journals if len(journals) == 1 else False

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.map_id = self.env['kit.statement.import.map'].search(
            [('journal_id', '=', self.journal_id.id)], limit=1) if self.journal_id else False

    @api.onchange('map_id')
    def _onchange_map_id(self):
        fmt = self.map_id
        if fmt:
            self.update({'encoding': fmt.encoding, 'delimiter': fmt.delimiter,
                         'decimal_separator': fmt.decimal_separator,
                         'date_format': fmt.date_format, 'skip_rows': fmt.skip_rows,
                         'reverse_sign': fmt.reverse_sign})

    # ------------------------------------------------------------------
    # Value parsing
    # ------------------------------------------------------------------
    def _parse_date(self, value, row=None, date_format='auto'):
        """Read a date; raise with the row number when it can't be read."""
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        text = str(value or '').strip().strip('"').strip("'")
        if date_format and date_format != 'auto':
            formats_to_try = (date_format,)
        else:
            formats_to_try = AUTO_DATE_FORMATS
        for fmt in formats_to_try:
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        raise UserError(self._row_error(
            row, _("cannot read the date '%s'.", text)))

    def _parse_float(self, value, row=None, decimal=None):
        """Read an amount: currency symbols, spaces, apostrophes and
        accounting negatives "(100.00)" or "100.00-" allowed. ``decimal``
        is the decimal sign; without it a comma is read as a decimal sign
        only in amounts like "1.234,56" or "12,5"."""
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value or '').strip().replace('"', '').replace("'", '')
        text = re.sub(r'[\s  $€£¥₹]|[A-Z]{3}', '', text)
        negative = False
        if text.startswith('(') and text.endswith(')'):
            text, negative = text[1:-1], True
        if text.endswith('-'):
            text, negative = text[:-1], True
        if decimal is None:
            decimal = ',' if re.fullmatch(
                r'[+-]?(\d{1,3}(\.\d{3})+|\d+),\d{1,2}', text) else '.'
        thousands = ',' if decimal == '.' else '.'
        text = text.replace(thousands, '').replace(decimal, '.')
        try:
            amount = float(text)
        except ValueError:
            raise UserError(self._row_error(
                row, _("cannot read the amount '%s'.", value))) from None
        return -amount if negative else amount

    def _row_error(self, row, message):
        if not row:
            return message
        return _("Row %(row)s: %(message)s", row=row, message=message)

    # ------------------------------------------------------------------
    # CSV / XLSX
    # ------------------------------------------------------------------
    def _decode(self, data, encoding='auto'):
        if encoding and encoding != 'auto':
            try:
                return data.decode('utf-16' if encoding == 'utf-16' else encoding)
            except (UnicodeDecodeError, LookupError):
                raise UserError(_("The file is not in %s; choose another "
                                  "encoding.", encoding)) from None
        for candidate in ('utf-8-sig', 'cp1252', 'latin-1'):
            try:
                return data.decode(candidate)
            except UnicodeDecodeError:
                continue
        return data.decode('latin-1', errors='replace')

    def _read_table(self, extension, data, options):
        """Rows of a CSV or XLSX file: (header, rows, number of the first
        data row)."""
        skip = options.get('skip_rows') or 0
        if extension == '.csv':
            text = self._decode(data, options.get('encoding'))
            if text.startswith('﻿'):
                text = text[1:]
            delimiter = options.get('delimiter') or 'auto'
            if delimiter == 'auto':
                lines = text.splitlines()[skip:skip + 20]
                try:
                    dialect = csv.Sniffer().sniff('\n'.join(lines), delimiters=',;\t|')
                except csv.Error:
                    dialect = csv.excel
                rows = list(csv.reader(io.StringIO(text), dialect))
            else:
                rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
        else:
            try:
                sheet = openpyxl.load_workbook(
                    filename=io.BytesIO(data), read_only=True,
                    data_only=True).active
            except Exception as error:
                raise UserError(_("Cannot read the XLSX file: %s", error)) from None
            rows = [list(row) for row in sheet.iter_rows(values_only=True)]
        rows = rows[skip:]
        if not rows:
            return [], [], skip + 2
        return rows[0], rows[1:], skip + 2

    @staticmethod
    def _normalise(title):
        return str(title if title is not None else '').strip().lower()

    def _guess_columns(self, header):
        """{value: column index} from the accepted column titles."""
        names = [self._normalise(h) for h in header]
        index = {}
        for key, aliases in HEADERS.items():
            for alias in aliases:
                if alias in names and names.index(alias) not in index.values():
                    index[key] = names.index(alias)
                    break
        return index

    def _columns_index(self, header, columns):
        """{value: column index} from {value: column title}; raise when a
        title isn't in the file."""
        names = [self._normalise(h) for h in header]
        index = {}
        for key, title in columns.items():
            if self._normalise(title) not in names:
                raise UserError(_(
                    "The column '%(column)s' of the format is not in the file. "
                    "Columns found: %(found)s.", column=title,
                    found=', '.join(str(h) for h in header if h not in (None, ''))))
            index[key] = names.index(self._normalise(title))
        return index

    @staticmethod
    def _has_amount(index):
        return 'date' in index and ('amount' in index or 'debit' in index or 'credit' in index)

    def _parse_rows(self, header, rows, first_row, index, options):
        """Transactions of CSV/XLSX rows; ``index`` gives the column of
        each value."""
        if not self._has_amount(index):
            raise UserError(_(
                "The file needs a date column and an amount column (or debit "
                "and credit columns). Accepted headers: date: %(date)s; "
                "amount: %(amount)s; debit: %(debit)s; credit: %(credit)s. "
                "Or use Set Columns to say which column holds what.",
                date=', '.join(HEADERS['date']),
                amount=', '.join(HEADERS['amount']),
                debit=', '.join(HEADERS['debit']),
                credit=', '.join(HEADERS['credit'])))
        decimal = options.get('decimal')
        date_format = options.get('date_format')

        def cell(values, key):
            i = index.get(key)
            if i is None or i >= len(values):
                return None
            value = values[i]
            return value.strip() if isinstance(value, str) else value

        def number(value, row):
            if value in (None, ''):
                return 0.0
            return self._parse_float(value, row, decimal)

        transactions = []
        balance_start = balance_end = None
        for row, values in enumerate(rows, start=first_row):
            values = list(values)
            if not any(str(v).strip() for v in values if v is not None):
                continue
            if 'amount' in index:
                amount = number(cell(values, 'amount'), row)
            else:
                amount = number(cell(values, 'credit'), row) - abs(number(cell(values, 'debit'), row))
            if options.get('reverse'):
                amount = -amount
            label = cell(values, 'label')
            ref = cell(values, 'reference')
            uid = cell(values, 'unique_id')
            transactions.append({
                'date': self._parse_date(cell(values, 'date'), row, date_format),
                'amount': amount,
                'payment_ref': str(label or ref or '/'),
                'partner_name': str(cell(values, 'partner') or '') or False,
                'account_number': str(cell(values, 'partner_account') or '') or False,
                'ref': str(ref) if ref not in (None, '') else False,
                'unique_id': str(uid) if uid not in (None, '') else False,
                'transaction_details': False,
            })
            start = cell(values, 'balance_start')
            if balance_start is None and start not in (None, ''):
                balance_start = self._parse_float(start, row, decimal)
            end = cell(values, 'balance')
            if end not in (None, ''):
                # running balance: the last row holds the end balance
                balance_end = self._parse_float(end, row, decimal)
        return [self._statement(transactions, balance_start, balance_end)]

    @staticmethod
    def _statement(transactions, balance_start=None, balance_end=None,
                   currency=None, account_number=None, name=None):
        return {'name': name, 'account_number': account_number,
                'currency': currency, 'balance_start': balance_start,
                'balance_end': balance_end, 'transactions': transactions}

    def _parse_old_xlsx(self, rows):
        """Earlier kit layout without known titles: label, amount, date,
        partner (first row is a title row)."""
        transactions = []
        for row, values in enumerate(rows[1:], start=2):
            values = list(values) + [None] * 4
            if not any(values[:4]):
                continue
            if not values[0]:
                raise UserError(self._row_error(row, _("the label is not set.")))
            transactions.append({
                'date': self._parse_date(values[2], row),
                'amount': self._parse_float(values[1], row),
                'payment_ref': str(values[0]),
                'partner_name': str(values[3]) if values[3] else False,
                'account_number': False, 'ref': False, 'unique_id': False,
                'transaction_details': False,
            })
        return [self._statement(transactions)]

    def _table_settings(self, journal):
        """(options, {value: column title} or None) for CSV / XLSX: the
        columns chosen in the wizard, else the journal's saved format, else
        None (column titles guessed)."""
        if self.state == 'columns':
            columns = {line.field: line.name for line in self.column_ids if line.field}
            return self._read_options(), columns
        fmt = self.map_id if self.map_id and self.map_id.journal_id == journal else \
            self.env['kit.statement.import.map'].search([('journal_id', '=', journal.id)], limit=1)
        if fmt:
            return fmt._read_options(), fmt._columns()
        options = self._read_options()
        if self.decimal_separator == 'point':
            options['decimal'] = None  # guessed per amount
        return options, None

    def _parse_table(self, extension, data, journal):
        options, columns = self._table_settings(journal)
        header, rows, first_row = self._read_table(extension, data, options)
        if not header:
            return [self._statement([])]
        if columns is not None:
            index = self._columns_index(header, columns)
        else:
            index = self._guess_columns(header)
            if extension == '.xlsx' and 'date' not in index:
                return self._parse_old_xlsx([header] + rows)
            if not self._has_amount(index):
                raise _NeedColumns(header, rows[:3])
        return self._parse_rows(header, rows, first_row, index, options)

    # ------------------------------------------------------------------
    # OFX / QIF / CAMT / MT940
    # ------------------------------------------------------------------
    def _parse_ofx(self, data):
        try:
            ofx = OfxParser.parse(io.BytesIO(data))
        except Exception as error:
            raise UserError(_("Cannot read the OFX file: %s", error)) from None
        statements = []
        for account in ofx.accounts or [ofx.account]:
            statement = account.statement if account else None
            if not statement:
                continue
            transactions = []
            for trans in statement.transactions:
                label = (trans.memo or trans.payee or '').strip()
                transactions.append({
                    'date': self._parse_date(trans.date),
                    'amount': float(trans.amount),
                    'payment_ref': label or '/',
                    'partner_name': (trans.payee or '').strip() or False,
                    'account_number': False,
                    'ref': trans.checknum or False,
                    'unique_id': trans.id or False,
                    'transaction_details': {'format': 'ofx', 'type': trans.type} if trans.type else False,
                })
            balance = getattr(statement, 'balance', None)
            statements.append(self._statement(
                transactions, None, float(balance) if balance is not None else None,
                (getattr(statement, 'currency', '') or '').upper() or None,
                getattr(account, 'number', None) or None))
        if not statements:
            raise UserError(_("No account statement found in the OFX file."))
        return statements

    def _parse_qif(self, data):
        text = self._decode(data).replace('\r\n', '\n').replace('\r', '\n')
        if not text.strip():
            return [self._statement([])]
        try:
            qif = QifParser.parse(io.StringIO(text))
        except Exception as error:
            raise UserError(_("Cannot read the QIF file: %s", error)) from None
        # Transactions sit on the file and on its accounts, grouped by
        # header ("!Type:Bank" ...).
        groups = list(qif._transactions.values())
        for account in qif.get_accounts():
            groups += list(account._transactions.values())
        transactions = []
        for group in groups:
            for trans in group:
                if trans.amount is None or not trans.date:
                    continue
                label = (trans.payee or trans.memo or '').strip()
                transactions.append({
                    'date': self._parse_date(trans.date),
                    'amount': float(trans.amount),
                    'payment_ref': label or '/',
                    'partner_name': (trans.payee or '').strip() or False,
                    'account_number': False,
                    'ref': getattr(trans, 'num', False) or False,
                    'unique_id': False,
                    'transaction_details': False,
                })
        return [self._statement(transactions)]

    def _parse_bank_format(self, reader, data):
        try:
            return reader(data)
        except ValueError as error:
            raise UserError(str(error)) from None

    def _parse(self, name, data, journal):
        """Statements of one file, by content first, then by extension."""
        extension = os.path.splitext(name or '')[1].lower()
        if formats.looks_like_camt(data):
            return self._parse_bank_format(formats.parse_camt, data)
        if extension not in TABLE_EXTENSIONS and formats.looks_like_mt940(data):
            return self._parse_bank_format(formats.parse_mt940, data)
        if extension == '.ofx':
            return self._parse_ofx(data)
        if extension == '.qif':
            return self._parse_qif(data)
        if extension in TABLE_EXTENSIONS:
            if not journal:
                raise UserError(_("Choose the journal: %s has no account number "
                                  "to find it from.", name))
            return self._parse_table(extension, data, journal)
        raise UserError(_("%(file)s can't be read: choose a %(types)s file.",
                          file=name, types=FILE_TYPES))

    # ------------------------------------------------------------------
    # Journal and duplicates
    # ------------------------------------------------------------------
    @staticmethod
    def _account_matches(journal_number, file_number):
        """The file's account is the journal's: same number once cleaned,
        or the IBAN ends with the domestic number of the file (MT940 often
        gives 'bank code/account')."""
        journal_number = sanitize_account_number(journal_number) or ''
        candidates = {sanitize_account_number(file_number) or ''}
        if '/' in file_number:
            candidates.add(sanitize_account_number(file_number.split('/')[-1]) or '')
        for candidate in filter(None, candidates):
            if candidate == journal_number:
                return True
            if candidate.isdigit() and len(candidate) >= 6 and re.match(r'^[A-Z]{2}\d{2}', journal_number):
                bban = journal_number[4:]
                if bban.lstrip('0').endswith(candidate.lstrip('0')):
                    return True
        return False

    def _journal_for(self, statement, name):
        """The wizard's journal, checked against the file's account; else
        the journal holding that account."""
        number = statement.get('account_number')
        journal = self.journal_id
        if journal:
            own = journal.bank_account_id.account_number
            if number and own and not self._account_matches(own, number):
                raise UserError(_(
                    "%(file)s is for the account %(account)s, but the journal "
                    "%(journal)s is for %(own)s.", file=name, account=number,
                    journal=journal.display_name, own=own))
            return journal
        if not number:
            raise UserError(_("Choose the journal: %s has no account number "
                              "to find it from.", name))
        candidates = self.env['account.journal'].search([
            ('company_id', 'in', self.env.companies.ids),
            ('bank_account_id', '!=', False),
            ('type', 'in', STATEMENT_JOURNAL_TYPES),
        ])
        journals = candidates.filtered(
            lambda j: self._account_matches(j.bank_account_id.account_number, number))
        if len(journals) != 1:
            raise UserError(_(
                "No single journal has the account %(account)s of %(file)s. "
                "Set it as the journal's bank account, or choose the journal.",
                account=number, file=name))
        return journals

    def _import_keys(self, journal, transactions):
        """Duplicate key of each transaction: the bank's transaction ID when
        the file has one, else date + amount + label + its occurrence number
        in the file (two identical lines stay two); prefixed with the
        journal."""
        seen = Counter()
        for trans in transactions:
            if trans['unique_id']:
                key = 'id|%s' % trans['unique_id']
            else:
                base = '%s|%.2f|%s' % (trans['date'], trans['amount'],
                                       trans['payment_ref'])
                seen[base] += 1
                key = '%s|%d' % (base, seen[base])
            trans['import_key'] = '%s|%s' % (journal.id, key)

    def _find_partner(self, name, account_number=False):
        """Partner owning the counterpart bank account, else the only
        partner with exactly this name."""
        Partner = self.env['res.partner']
        if account_number:
            banks = self.env['res.partner.bank'].search([
                ('sanitized_account_number', '=', sanitize_account_number(account_number))], limit=2)
            if len(banks.partner_id) == 1:
                return banks.partner_id
        if not name:
            return Partner
        partners = Partner.search([('name', '=', name)], limit=2)
        return partners if len(partners) == 1 else Partner

    # ------------------------------------------------------------------
    # Statement creation
    # ------------------------------------------------------------------
    def _create_statement(self, journal, parsed, name, data):
        """One bank statement from one parsed statement; returns
        (statement or None, number of transactions skipped)."""
        journal_currency = journal.currency_id or journal.company_id.currency_id
        transactions = [t for t in parsed.get('transactions', [])
                        if not journal_currency.is_zero(t['amount'])]
        currency = parsed.get('currency')
        if currency and currency != journal_currency.name:
            raise UserError(_(
                "The file is in %(file)s but the journal %(journal)s is in "
                "%(currency)s.", file=currency, journal=journal.display_name,
                currency=journal_currency.name))
        if not transactions:
            return None, 0
        self._import_keys(journal, transactions)
        existing = set(self.env['account.bank.statement.line'].search([
            ('journal_id', '=', journal.id),
            ('kit_import_id', 'in', [t['import_key'] for t in transactions]),
        ]).mapped('kit_import_id'))
        new = [t for t in transactions if t['import_key'] not in existing]
        skipped = len(transactions) - len(new)
        if not new:
            return None, skipped

        total = sum(t['amount'] for t in new)
        attachment = self.env['ir.attachment'].create({
            'name': name, 'raw': data, 'res_model': 'account.bank.statement'})
        vals = {
            'name': parsed.get('statement_name') or os.path.splitext(name or '')[0] or _('Import'),
            'journal_id': journal.id,
            'attachment_ids': [Command.set(attachment.ids)],
            'line_ids': [Command.create({
                'date': t['date'],
                'payment_ref': t['payment_ref'],
                'amount': t['amount'],
                'partner_id': self._find_partner(t['partner_name'], t.get('account_number')).id,
                'partner_name': t['partner_name'],
                'account_number': t.get('account_number') or False,
                'ref': t['ref'],
                'transaction_details': t.get('transaction_details') or False,
                'journal_id': journal.id,
                'kit_import_id': t['import_key'],
            }) for t in sorted(new, key=lambda t: t['date'])],
        }
        balance_start = parsed.get('balance_start')
        balance_end = parsed.get('balance_end')
        if balance_end is not None:
            vals['balance_start'] = balance_end - total
            vals['balance_end_real'] = balance_end
        elif balance_start is not None and not skipped:
            vals['balance_start'] = balance_start
            vals['balance_end_real'] = balance_start + total
        statement = self.env['account.bank.statement'].with_company(
            journal.company_id).create(vals)
        if 'balance_end_real' not in vals:
            # Start balance computed by core from the previous statement.
            statement.balance_end_real = statement.balance_start + total
        return statement, skipped

    def _files(self):
        """[(name, content)] of the uploaded files."""
        files = [(attachment.name, attachment.raw.content if attachment.raw else b'')
                 for attachment in self.attachment_ids]
        if self.attachment or self.file_name:
            # Odoo 20: a Binary field reads as a BinaryValue holding the
            # decoded file content.
            files.append((self.file_name, self.attachment.content if self.attachment else b''))
        if not files:
            raise UserError(_("Choose the file to import."))
        return files

    def _import_files(self):
        """Import every file; returns (statements, summary lines,
        transactions skipped)."""
        statements = self.env['account.bank.statement']
        summary, skipped_total = [], 0
        files = self._files()
        for name, data in files:
            try:
                parsed_list = self._parse(name, data, self.journal_id)
            except _NeedColumns as need:
                if len(files) > 1:
                    raise UserError(_(
                        "The columns of %s are not known: import it alone to "
                        "say which column holds what.", name)) from None
                raise
            created, skipped, count = self.env['account.bank.statement'], 0, 0
            for number, parsed in enumerate(parsed_list, start=1):
                if len(parsed_list) > 1:
                    parsed['statement_name'] = '%s - %s' % (
                        os.path.splitext(name)[0], parsed.get('name') or number)
                journal = self._journal_for(parsed, name)
                statement, skip = self._create_statement(journal, parsed, name, data)
                skipped += skip
                count += len(parsed.get('transactions', []))
                if statement:
                    created |= statement
            if not count:
                raise UserError(_("The file contains no transactions.")
                                if len(files) == 1 else
                                _("%s contains no transactions.", name))
            statements |= created
            skipped_total += skipped
            summary.append(_("%(file)s: %(new)s imported, %(skipped)s already there.",
                             file=name, new=len(created.line_ids), skipped=skipped))
        if not statements:
            raise UserError(_("This file was already imported.") if len(files) == 1
                            else _("These files were already imported."))
        return statements, summary, skipped_total

    def _columns_step(self, need):
        """Show the file's columns so the user says which holds what."""
        self.column_ids = [Command.clear()] + [Command.create({
            'sequence': i,
            'name': str(title),
            'sample': ' | '.join(str(row[i]) for row in need.rows
                                 if i < len(row) and row[i] not in (None, ''))[:80],
            'field': next((key for key, aliases in HEADERS.items()
                           if self._normalise(title) in aliases and key in dict(COLUMN_FIELDS)), False),
        }) for i, title in enumerate(need.header) if title not in (None, '')]
        self.state = 'columns'
        if not self.map_name:
            self.map_name = _('%s format', self.journal_id.name)
        return self._reopen()

    def action_set_columns(self):
        """Choose the columns of a CSV / XLSX file by hand."""
        self.ensure_one()
        files = self._files()
        extension = os.path.splitext(files[0][0] or '')[1].lower()
        if len(files) != 1 or extension not in TABLE_EXTENSIONS:
            raise UserError(_("Set Columns works on one CSV or XLSX file."))
        if not self.journal_id:
            raise UserError(_("Choose the journal first."))
        header, rows, _first = self._read_table(extension, files[0][1], self._read_options())
        if not header:
            raise UserError(_("The file contains no transactions."))
        return self._columns_step(_NeedColumns(header, rows[:3]))

    def action_back(self):
        self.ensure_one()
        self.state = 'upload'
        return self._reopen()

    def _reopen(self):
        return {'type': 'ir.actions.act_window', 'name': _('Import Statement'),
                'res_model': self._name, 'res_id': self.id,
                'views': [(False, 'form')], 'target': 'new'}

    def _save_map(self):
        columns = {line.field: line.name for line in self.column_ids if line.field}
        self.env['kit.statement.import.map'].create({
            'name': self.map_name or _('%s format', self.journal_id.name),
            'journal_id': self.journal_id.id,
            'encoding': self.encoding,
            'delimiter': self.delimiter,
            'decimal_separator': self.decimal_separator,
            'date_format': self.date_format,
            'skip_rows': self.skip_rows,
            'reverse_sign': self.reverse_sign,
            **{'%s_column' % key: title for key, title in columns.items()},
        })

    def action_statement_import(self):
        """Import the files: one bank statement per statement in each file."""
        self.ensure_one()
        if self.state == 'columns':
            fields_chosen = [line.field for line in self.column_ids if line.field]
            duplicates = [key for key, count in Counter(fields_chosen).items() if count > 1]
            if duplicates:
                labels = dict(self.env['import.bank.statement.column']._fields['field']
                              ._description_selection(self.env))
                raise UserError(_("Several columns are set as %s.",
                                  ', '.join(labels[key] for key in duplicates)))
        try:
            statements, summary, skipped = self._import_files()
        except _NeedColumns as need:
            return self._columns_step(need)
        if self.state == 'columns' and self.save_map:
            self._save_map()
        reconciled = self.env['account.bank.statement.line']
        for company, company_statements in statements.grouped('company_id').items():
            if company.kit_auto_reconcile_import:
                reconciled |= company_statements.line_ids._auto_reconcile()
        action = self._statements_action(statements)
        if len(summary) == 1 and not skipped and not reconciled:
            return action
        message = ' '.join(summary)
        if reconciled:
            message += ' ' + _("%(count)s reconciled automatically.",
                               count=len(reconciled))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'warning' if skipped else 'success',
                'sticky': bool(skipped),
                'message': message,
                'next': action,
            },
        }

    def _statements_action(self, statements):
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Statements'),
            'res_model': 'account.bank.statement',
            'target': 'current',
        }
        if len(statements) == 1:
            action.update(res_id=statements.id, views=[(False, 'form')])
        else:
            action.update(domain=[('id', 'in', statements.ids)],
                          views=[(False, 'list'), (False, 'form')])
        return action


class ImportBankStatementColumn(models.TransientModel):
    """A column of the uploaded CSV / XLSX file and what it holds."""
    _name = 'import.bank.statement.column'
    _description = 'Statement File Column'
    _order = 'sequence'

    wizard_id = fields.Many2one('import.bank.statement', required=True, ondelete='cascade')
    sequence = fields.Integer()
    name = fields.Char(string="Column", readonly=True)
    sample = fields.Char(string="First Values", readonly=True)
    field = fields.Selection(COLUMN_FIELDS, string="Holds")


class _NeedColumns(Exception):
    """The columns of a CSV / XLSX file are not known."""

    def __init__(self, header, rows):
        super().__init__()
        self.header = header
        self.rows = rows
