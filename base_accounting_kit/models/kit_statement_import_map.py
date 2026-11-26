# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
"""Saved CSV / XLSX statement formats, one or more per journal: how to read
the file (encoding, separators, date format, lines above the header) and
which column holds what."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# Statement line values a column can hold.
COLUMN_FIELDS = [
    ('date', 'Date'),
    ('amount', 'Amount'),
    ('debit', 'Money out'),
    ('credit', 'Money in'),
    ('label', 'Label'),
    ('partner', 'Partner name'),
    ('partner_account', 'Partner account'),
    ('reference', 'Reference'),
    ('unique_id', 'Transaction ID'),
    ('balance', 'Balance'),
]
DATE_FORMATS = [
    ('auto', 'Automatic'),
    ('ymd_dash', '2026-03-31'),
    ('dmy_slash', '31/03/2026'),
    ('mdy_slash', '03/31/2026'),
    ('dmy_dot', '31.03.2026'),
    ('dmy_dash', '31-03-2026'),
    ('ymd_slash', '2026/03/31'),
    ('dmy_slash_short', '31/03/26'),
    ('mdy_slash_short', '03/31/26'),
    ('dmy_dot_short', '31.03.26'),
    ('ymd_compact', '20260331'),
]
# strptime pattern of each date format.
DATE_PATTERNS = {
    'ymd_dash': '%Y-%m-%d', 'dmy_slash': '%d/%m/%Y', 'mdy_slash': '%m/%d/%Y',
    'dmy_dot': '%d.%m.%Y', 'dmy_dash': '%d-%m-%Y', 'ymd_slash': '%Y/%m/%d',
    'dmy_slash_short': '%d/%m/%y', 'mdy_slash_short': '%m/%d/%y',
    'dmy_dot_short': '%d.%m.%y', 'ymd_compact': '%Y%m%d',
}
DELIMITERS = {'comma': ',', 'semicolon': ';', 'tab': '\t', 'pipe': '|'}
DECIMALS = {'point': '.', 'comma': ','}


class KitStatementImportOptions(models.AbstractModel):
    """How a CSV / XLSX statement file is read; shared by the saved format
    and the import wizard."""
    _name = 'kit.statement.import.options'
    _description = 'Statement File Options'

    encoding = fields.Selection([
        ('auto', 'Automatic'), ('utf-8', 'UTF-8'),
        ('cp1252', 'Windows-1252'), ('iso-8859-1', 'Latin-1 (ISO 8859-1)'),
        ('utf-16', 'UTF-16')], default='auto', required=True,
        help="Character set of CSV files. Automatic tries UTF-8, then "
             "Windows-1252.")
    delimiter = fields.Selection([
        ('auto', 'Automatic'), ('comma', 'Comma'), ('semicolon', 'Semicolon'),
        ('tab', 'Tab'), ('pipe', 'Pipe')], default='auto', required=True,
        string="Column Separator")
    decimal_separator = fields.Selection([
        ('point', 'Point (1,234.56)'), ('comma', 'Comma (1.234,56)')],
        default='point', required=True,
        help="The other sign, spaces and apostrophes are read as thousands "
             "separators.")
    date_format = fields.Selection(DATE_FORMATS, default='auto', required=True)
    skip_rows = fields.Integer(
        string="Lines Above the Header",
        help="Lines the bank puts above the column titles (account, period...).")
    reverse_sign = fields.Boolean(
        string="Reverse Amount Sign",
        help="For files that show money out as positive amounts.")

    @api.constrains('skip_rows')
    def _check_skip_rows(self):
        if any(record.skip_rows < 0 for record in self):
            raise ValidationError(_("Lines above the header can't be negative."))

    def _read_options(self):
        """Options as a plain dict for the readers."""
        self.ensure_one()
        return {
            'encoding': self.encoding,
            'delimiter': DELIMITERS.get(self.delimiter, 'auto'),
            'decimal': DECIMALS[self.decimal_separator],
            'date_format': DATE_PATTERNS.get(self.date_format, 'auto'),
            'skip_rows': self.skip_rows,
            'reverse': self.reverse_sign,
        }


class KitStatementImportMap(models.Model):
    """A saved CSV / XLSX format of a bank journal."""
    _name = 'kit.statement.import.map'
    _inherit = ['kit.statement.import.options']
    _description = 'Statement Import Format'
    _order = 'journal_id, sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    journal_id = fields.Many2one(
        'account.journal', required=True, ondelete='cascade', index=True,
        domain="[('type', 'in', ('bank', 'cash', 'credit'))]",
        help="The first active format of the journal is used for its CSV and "
             "XLSX files.")
    company_id = fields.Many2one(related='journal_id.company_id', store=True)
    date_column = fields.Char(required=True, help="Title of the column, as in the file.")
    amount_column = fields.Char(help="Signed amount. Leave empty when the file has money in / money out columns.")
    debit_column = fields.Char(string="Money Out Column")
    credit_column = fields.Char(string="Money In Column")
    label_column = fields.Char()
    partner_column = fields.Char(string="Partner Name Column")
    partner_account_column = fields.Char()
    reference_column = fields.Char()
    unique_id_column = fields.Char(
        string="Transaction ID Column",
        help="Bank's own ID of each transaction; used to skip lines already imported.")
    balance_column = fields.Char(help="Running balance; the last line gives the ending balance.")

    @api.constrains('amount_column', 'debit_column', 'credit_column')
    def _check_amount_column(self):
        for record in self:
            if not (record.amount_column or record.debit_column or record.credit_column):
                raise ValidationError(_(
                    "The format %s needs an amount column, or money in / money out columns.",
                    record.name))

    def _columns(self):
        """{value: column title} of the format."""
        self.ensure_one()
        return {key: self['%s_column' % key].strip()
                for key, _label in COLUMN_FIELDS if self['%s_column' % key]}
