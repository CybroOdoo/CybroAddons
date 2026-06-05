# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAccountJournal(TransactionCase):
    """Test journal sequence linkage."""

    def test_journal_sequence_onchange_keeps_character_month_prefix(self):
        """Journal onchange preserves tokenized sequence prefixes."""
        sequence = self.env['ir.sequence'].create({
            'name': 'Test Journal Character Month Sequence',
            'code': 'test.journal.character.month.sequence',
            'prefix': 'INV/%(month_name)s',
        })
        journal = self.env['account.journal'].new({
            'name': 'Test Character Month Journal',
            'code': 'TCM',
            'type': 'sale',
            'sequence_id': sequence,
        })

        journal._onchange_sequence_id()

        self.assertEqual(
            journal.code,
            'INV/%',
            "Journal code should keep Odoo's existing short-code behavior."
        )
        self.assertEqual(
            sequence.prefix,
            'INV/%(month_name)s',
            "Sequence prefix should keep the month name token."
        )

    def test_journal_sequence_onchange_updates_code_for_short_prefix(self):
        """Simple sequence prefixes still update the journal short code."""
        sequence = self.env['ir.sequence'].create({
            'name': 'Test Journal Short Sequence',
            'code': 'test.journal.short.sequence',
            'prefix': 'BILL',
        })
        journal = self.env['account.journal'].new({
            'name': 'Test Short Prefix Journal',
            'code': 'TCJ',
            'type': 'sale',
            'sequence_id': sequence,
        })

        journal._onchange_sequence_id()

        self.assertEqual(
            journal.code,
            'BILL',
            "Journal code should still follow simple short sequence prefixes."
        )
