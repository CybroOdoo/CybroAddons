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
#############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestPosIdleTimeSessionLock(common.TransactionCase):
    """Test cases for POS Idle Session Lock configuration and constraints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Idle Lock Shop',
        })

    def test_default_config_values(self):
        """Test default values for pos_lock and idle_time_limit."""
        self.assertFalse(self.pos_config.pos_lock)
        self.assertEqual(self.pos_config.idle_time_limit, 10)

    def test_enable_pos_lock(self):
        """Test enabling pos_lock with a valid idle time limit."""
        self.pos_config.write({
            'pos_lock': True,
            'idle_time_limit': 15,
        })
        self.assertTrue(self.pos_config.pos_lock)
        self.assertEqual(self.pos_config.idle_time_limit, 15)

    def test_idle_time_limit_zero_raises_error_when_locked(self):
        """Test that idle_time_limit <= 0 raises ValidationError when locked."""
        with self.assertRaises(ValidationError):
            self.pos_config.write({
                'pos_lock': True,
                'idle_time_limit': 0,
            })

    def test_idle_time_limit_negative_raises_error_when_locked(self):
        """Test that negative idle_time_limit raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.pos_config.write({
                'pos_lock': True,
                'idle_time_limit': -5,
            })

    def test_zero_idle_time_limit_allowed_when_lock_disabled(self):
        """Test that zero idle_time_limit is permitted when lock is off."""
        self.pos_config.write({
            'pos_lock': False,
            'idle_time_limit': 0,
        })
        self.assertFalse(self.pos_config.pos_lock)
        self.assertEqual(self.pos_config.idle_time_limit, 0)
