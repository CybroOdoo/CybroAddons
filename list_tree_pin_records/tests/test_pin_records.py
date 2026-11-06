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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPinRecords(TransactionCase):
    """Unit tests for the pin.records model."""

    def setUp(self):
        super().setUp()
        self.PinRecord = self.env['pin.records']
        self.user = self.env.ref('base.user_demo', raise_if_not_found=False)
        if not self.user:
            self.user = self.env['res.users'].create({
                'name': 'Pin Test User',
                'login': 'pin_test_user',
                'email': 'pin_test_user@example.com',
                'group_ids': [(4, self.env.ref('base.group_user').id)],
            })
        self.res_model = 'res.partner'


    def test_pin_record_returns_empty_list_when_no_pins(self):
        """pin_record returns an empty list when no records are pinned."""
        result = self.PinRecord.with_user(self.user).pin_record(
            self.res_model
        )
        self.assertEqual(result, [])

    def test_pin_record_returns_pinned_records(self):
        """pin_record returns the pinned records for the current user."""
        self.PinRecord.with_user(self.user).create({
            'record_id': 42,
            'res_model': self.res_model,
            'color': '#4AEBC8',
            'user_id': self.user.id,
        })
        result = self.PinRecord.with_user(self.user).pin_record(
            self.res_model
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 42)
        self.assertEqual(result[0]['model'], self.res_model)

    def test_pin_record_isolated_per_user(self):
        """pin_record does not return pins belonging to another user."""
        other_user = self.env.ref('base.user_root')
        self.PinRecord.with_user(other_user).create({
            'record_id': 99,
            'res_model': self.res_model,
            'color': '',
            'user_id': other_user.id,
        })
        result = self.PinRecord.with_user(self.user).pin_record(
            self.res_model
        )
        self.assertEqual(result, [])

    # ------------------------------------------------------------------
    # save_pin_record
    # ------------------------------------------------------------------

    def test_save_pin_record_creates_new_pin(self):
        """save_pin_record creates a new pin with color when none exists."""
        self.PinRecord.with_user(self.user).save_pin_record(
            [1, self.res_model, '#4AEBC8']
        )
        pins = self.PinRecord.search([
            ('record_id', '=', 1),
            ('res_model', '=', self.res_model),
            ('user_id', '=', self.user.id),
        ])
        self.assertEqual(len(pins), 1)
        self.assertEqual(pins.color, '#4AEBC8')

    def test_save_pin_record_removes_existing_pin(self):
        """save_pin_record deletes the record if it is already pinned."""
        self.PinRecord.with_user(self.user).save_pin_record(
            [2, self.res_model]
        )
        # Call again to toggle off
        self.PinRecord.with_user(self.user).save_pin_record(
            [2, self.res_model]
        )
        pins = self.PinRecord.search([
            ('record_id', '=', 2),
            ('res_model', '=', self.res_model),
            ('user_id', '=', self.user.id),
        ])
        self.assertEqual(len(pins), 0)

    def test_save_pin_record_does_not_affect_other_users(self):
        """save_pin_record toggle is scoped to the current user only."""
        other_user = self.env.ref('base.user_root')
        # Create a pin for another user directly
        self.PinRecord.with_user(other_user).create({
            'record_id': 3,
            'res_model': self.res_model,
            'color': '',
            'user_id': other_user.id,
        })
        # Current user toggles: should create, not delete the other user's pin
        self.PinRecord.with_user(self.user).save_pin_record(
            [3, self.res_model]
        )
        other_pins = self.PinRecord.search([
            ('record_id', '=', 3),
            ('res_model', '=', self.res_model),
            ('user_id', '=', other_user.id),
        ])
        self.assertEqual(
            len(other_pins), 1, "Other user's pin must not be deleted"
        )

    def test_save_pin_record_isolated_by_model(self):
        """Pins for different models are independent."""
        other_model = 'res.company'
        self.PinRecord.with_user(self.user).save_pin_record(
            [5, self.res_model]
        )
        self.PinRecord.with_user(self.user).save_pin_record(
            [5, other_model]
        )
        # Toggle off only for res_model
        self.PinRecord.with_user(self.user).save_pin_record(
            [5, self.res_model]
        )
        remaining = self.PinRecord.search([
            ('record_id', '=', 5),
            ('user_id', '=', self.user.id),
        ])
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining.res_model, other_model)

    def test_save_pin_record_handles_invalid_input(self):
        """save_pin_record gracefully handles empty or incomplete input."""
        res_empty = self.PinRecord.with_user(self.user).save_pin_record([])
        self.assertFalse(res_empty)
        res_single = self.PinRecord.with_user(self.user).save_pin_record([1])
        self.assertFalse(res_single)
        res_none = self.PinRecord.with_user(self.user).save_pin_record(None)
        self.assertFalse(res_none)
