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
from datetime import date

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAccountMove(TransactionCase):
    """Test account move names with journal sequence month tokens."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sequence = cls.env['ir.sequence'].create({
            'name': 'Test Move Character Month Sequence',
            'code': 'test.move.character.month.sequence',
            'prefix': 'INV/%(month_name)s',
            'suffix': '%(month_abbr)s',
            'number_increment': 1,
        })
        cls.journal = cls.env['account.journal'].create({
            'name': 'Test Move Character Month Journal',
            'code': 'TMM',
            'type': 'sale',
            'sequence_id': cls.sequence.id,
        })

    def test_starting_sequence_uses_character_month_tokens(self):
        """Fallback starting sequence uses interpolated prefix and suffix."""
        move_date = date(2026, 5, 19)
        move = self.env['account.move'].create({
            'journal_id': self.journal.id,
            'move_type': 'out_invoice',
            'date': move_date,
        })

        self.assertEqual(
            move._get_starting_sequence(),
            'INV/%s/2026/1%s' % (
                move_date.strftime('%B'),
                move_date.strftime('%b'),
            ),
            "Starting sequence should include character month values."
        )

    def test_next_sequence_uses_move_date_for_character_month_tokens(self):
        """Generated move name uses the account move date for month tokens."""
        move_date = date(2026, 5, 19)
        move = self.env['account.move'].create({
            'journal_id': self.journal.id,
            'move_type': 'out_invoice',
            'date': move_date,
        })

        move._set_next_sequence()

        self.assertEqual(
            move.name,
            'INV/%s/2026/1/%s' % (
                move_date.strftime('%B'),
                move_date.strftime('%b'),
            ),
            "Move name should use month name and abbreviation tokens."
        )
