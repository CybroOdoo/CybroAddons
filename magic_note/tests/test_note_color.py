# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestNoteColor(TransactionCase):

    def test_check_interval_dates_valid(self):
        """Test that a valid interval does not raise a validation error."""
        today = fields.Date.today()
        record = self.env['note.color'].create({
            'name': 'Test Valid Interval',
            'start_interval': today,
            'end_interval': today + timedelta(days=5),
        })
        self.assertTrue(record.id)

    def test_check_interval_dates_invalid(self):
        """Test that start_date > end_date raises a ValidationError."""
        today = fields.Date.today()
        with self.assertRaises(
            ValidationError,
            msg="Lower Limit should not be greater than Upper Limit."
        ):
            self.env['note.color'].create({
                'name': 'Test Invalid Interval',
                'start_interval': today + timedelta(days=5),
                'end_interval': today,
            })
