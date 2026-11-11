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
from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestScheduledActionShortcut(TransactionCase):
    """Test suite for running scheduled actions from the systray shortcut,

    covering the systray flag, the systray listing, direct execution,
    error reporting and access rights.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Systray Partner',
        })
        cls.cron = cls.env['ir.cron'].create(cls._get_cron_vals(
            'Test Systray Cron',
            f"model.browse({cls.partner.id}).write("
            f"{{'name': 'Updated From Systray'}})",
        ))
        cls.internal_user = new_test_user(
            cls.env, login='systray_internal_user', groups='base.group_user')

    @classmethod
    def _get_cron_vals(cls, name, code):
        """Return the values needed to create a test scheduled action."""
        return {
            'name': name,
            'state': 'code',
            'code': code,
            'model_id': cls.env.ref('base.model_res_partner').id,
            'user_id': cls.env.uid,
            'active': True,
            'interval_number': 1,
            'interval_type': 'days',
            'nextcall': fields.Datetime.now() + timedelta(hours=1),
        }

    def test_01_systray_flag_toggle(self):
        """Verify the systray flag is disabled by default and can be toggled."""
        self.assertFalse(self.cron.run_through_systray)

        self.cron.write({'run_through_systray': True})
        self.assertTrue(self.cron.run_through_systray)

        self.cron.write({'run_through_systray': False})
        self.assertFalse(self.cron.run_through_systray)

    def test_02_systray_lists_only_enabled_actions(self):
        """Verify the systray domain only returns actions enabled for it."""
        other_cron = self.env['ir.cron'].create(
            self._get_cron_vals('Test Hidden Cron', ''))
        self.cron.write({'run_through_systray': True})

        # Same domain and fields as the systray component uses
        actions = self.env['ir.cron'].search_read(
            [('run_through_systray', '=', True)], ['cron_name', 'nextcall'])
        action_ids = [action['id'] for action in actions]
        self.assertIn(self.cron.id, action_ids)
        self.assertNotIn(other_cron.id, action_ids)

        listed = next(a for a in actions if a['id'] == self.cron.id)
        self.assertEqual(listed['cron_name'], 'Test Systray Cron')

    def test_03_run_scheduled_action(self):
        """Verify running from the systray executes the action code."""
        self.cron.write({'run_through_systray': True})
        with self.registry_test_mode():
            result = self.cron.run_scheduled_actions()

        self.assertIs(result, True)
        self.assertEqual(self.partner.name, 'Updated From Systray')

    @mute_logger('odoo.addons.base.models.ir_cron')
    def test_04_run_scheduled_action_failure(self):
        """Verify a failing action returns an error action, not success."""
        failing_cron = self.env['ir.cron'].create(self._get_cron_vals(
            'Test Failing Cron', "raise UserError('Systray failure')"))
        with self.registry_test_mode(), \
                self.registry.cursor() as cron_cr:
            result = failing_cron.with_env(
                self.env(cr=cron_cr)).run_scheduled_actions()

        self.assertIsNot(result, True)
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_exception')

    def test_05_internal_user_cannot_run_action(self):
        """Verify a user without write access cannot run scheduled actions."""
        with self.assertRaises(AccessError):
            self.cron.with_user(self.internal_user).run_scheduled_actions()

    def test_06_form_view_shows_systray_flag(self):
        """Verify the scheduled action form view displays the systray flag."""
        arch = self.env['ir.cron'].get_view(view_type='form')['arch']
        self.assertIn('run_through_systray', arch)
