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
from datetime import datetime

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestIrSequence(TransactionCase):
    """Test custom journal sequence interpolation."""

    def test_month_character_tokens_in_prefix_and_suffix(self):
        """Month name tokens are interpolated alongside numeric month."""
        sequence_date = datetime(2026, 5, 19, 10, 30, 0)
        sequence = self.env['ir.sequence'].create({
            'name': 'Test Character Month Sequence',
            'code': 'test.character.month.sequence',
            'prefix': 'INV/%(month_name)s/%(month)s/',
            'suffix': '/%(month_abbr)s',
        })

        prefix, suffix = sequence.with_context(
            ir_sequence_date=fields.Datetime.to_string(sequence_date)
        )._get_prefix_suffix()

        self.assertEqual(
            prefix,
            'INV/%s/05/' % sequence_date.strftime('%B'),
            "The full month name should be available in sequence prefixes."
        )
        self.assertEqual(
            suffix,
            '/%s' % sequence_date.strftime('%b'),
            "The abbreviated month name should be available in suffixes."
        )

    def test_month_character_tokens_support_date_ranges(self):
        """Character month tokens also work with range_ variables."""
        sequence_date = datetime(2026, 5, 19, 10, 30, 0)
        range_date = datetime(2026, 1, 1, 0, 0, 0)
        sequence = self.env['ir.sequence'].create({
            'name': 'Test Range Character Month Sequence',
            'code': 'test.range.character.month.sequence',
            'prefix': (
                'INV/%(range_month_name)s/%(range_month_abbr)s/'
                '%(month_abbr)s/'
            ),
        })

        prefix, suffix = sequence.with_context(
            ir_sequence_date=fields.Datetime.to_string(sequence_date),
            ir_sequence_date_range=fields.Datetime.to_string(range_date),
        )._get_prefix_suffix()

        self.assertEqual(
            prefix,
            'INV/%s/%s/%s/' % (
                range_date.strftime('%B'),
                range_date.strftime('%b'),
                sequence_date.strftime('%b'),
            ),
            "The range month name tokens should be interpolated."
        )
        self.assertEqual(
            suffix,
            '',
            "Empty sequence suffix should remain empty."
        )
