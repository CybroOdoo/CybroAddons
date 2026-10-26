# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import timedelta

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import EquipmentCommon


@tagged('post_install', '-at_install')
class TestMaintenanceRequest(EquipmentCommon):
    """GMP maintenance: engineering completes, QA releases."""

    def test_workflow(self):
        """New, In Progress, Completed, QA Verified; the stage mirrors the state."""
        machine = self.machine()
        request = self.request(machine, 'preventive',
                               stage_id=self.env.ref('maintenance.stage_3').id)
        self.assertEqual((request.pharma_state, request.stage_id),
                         ('new', self.env.ref('maintenance.stage_0')))
        with self.assertRaises(UserError):
            request.stage_id = self.env.ref('maintenance.stage_1')
        with self.assertRaises(UserError):
            request.action_pharma_complete()
        request.with_user(self.operator).action_pharma_start()
        self.assertEqual(request.stage_id, self.env.ref('maintenance.stage_1'))
        with self.assertRaises(UserError):
            request.action_pharma_start()
        with self.assertRaises(UserError):
            request.with_user(self.operator).action_pharma_complete()
        request.work_done = 'Replaced the gearbox oil.'
        with self.assertRaises(UserError):
            request.with_user(self.qa_only).action_qa_verify()
        request.with_user(self.operator).action_pharma_complete()
        self.assertEqual((request.pharma_state, request.completed_by), ('completed', self.operator))
        self.assertTrue(request.activity_ids)
        with self.assertRaises(AccessError):
            request.with_user(self.operator).action_qa_verify()
        request.with_user(self.qa_only).action_qa_verify()
        self.assertEqual((request.pharma_state, request.qa_verified_by, request.stage_id),
                         ('qa_verified', self.qa_only,
                          self.env.ref('pharma_equipment_maintenance.stage_pharma_qa_verified')))
        with self.assertRaises(UserError):
            request.archive_equipment_request()
        with self.assertRaises(UserError):
            request.unlink()

    def test_gates(self):
        """No equipment, a cancelled request or self-verification are refused."""
        machine = self.machine()
        loose = self.Request.with_user(self.qa_user).create({
            'name': 'No equipment', 'maintenance_type': 'corrective'})
        loose.action_pharma_start()
        loose.work_done = 'Checked.'
        with self.assertRaises(UserError):
            loose.action_pharma_complete()
        loose.equipment_id = machine
        loose.action_pharma_complete()
        with self.assertRaises(UserError):
            loose.with_user(self.qa_user).action_qa_verify()
        cancelled = self.request(machine, 'corrective')
        cancelled.archive_equipment_request()
        with self.assertRaises(UserError):
            cancelled.action_pharma_start()
        cancelled.reset_equipment_request()
        self.assertEqual((cancelled.archive, cancelled.pharma_state), (False, 'new'))
        cancelled.unlink()
        self.assertFalse(cancelled.exists())

    def test_breakdown_and_requalification(self):
        """An open breakdown makes equipment unfit; a repair may call for requalification."""
        machine = self.machine(iq_done=True, oq_done=True, pq_done=True,
                               qualification_date=self.days(-10), requalification_date=self.days(300))
        self.assertEqual(machine.action_raise_breakdown()['context']['default_maintenance_type'],
                         'corrective')
        breakdown = self.request(machine, 'corrective')
        self.assertTrue(machine.open_breakdown)
        self.assertIn(machine, self.Equipment.search([('open_breakdown', '=', True)]))
        self.assertNotIn(machine, self.Equipment.search([('open_breakdown', '!=', True)]))
        self.assertIn('under breakdown repair', machine._pharma_fitness_issues())
        breakdown.requalification_required = True
        self.complete(breakdown)
        self.assertFalse(machine.open_breakdown)
        self.assertEqual(machine.requalification_date, fields.Date.today())
        self.assertEqual(machine.qualification_state, 'requalification_due')
        self.assertIn('Requalification required after', machine.message_ids[0].body)

    def test_cleaning(self):
        """A verified cleaning makes equipment clean; holds carry over and expire."""
        machine = self.machine()
        self.assertEqual(machine.cleaning_state, 'dirty')
        self.assertIn('not clean', machine._pharma_fitness_issues())
        context = machine.action_raise_cleaning()['context']
        self.assertEqual(context['default_maintenance_type'], 'cleaning')
        first = self.request(machine, clean_hold_hours=48, dirty_hold_hours=4)
        first.with_user(self.operator).action_pharma_start()
        self.assertEqual(machine.cleaning_status, 'in_progress')
        first.work_done = 'Cleaned as per SOP-CLN-01.'
        first.with_user(self.operator).action_pharma_complete()
        first.with_user(self.qa_only).action_qa_verify()
        self.assertEqual((machine.cleaning_state, machine.last_cleaning_request_id),
                         ('clean', first))
        self.assertEqual(machine.clean_valid_until, first.completed_on + timedelta(hours=48))
        self.assertEqual(machine.action_view_cleanings()['domain'],
                         [('equipment_id', '=', machine.id), ('maintenance_type', '=', 'cleaning')])
        second = self.request(machine)
        self.assertEqual((second.clean_hold_hours, second.dirty_hold_hours), (48, 4))
        with self.assertRaises(ValidationError):
            second.clean_hold_hours = -1
        now = fields.Datetime.now()
        # States are stored when the data changes; the cron finds them stale later.
        self.env.flush_all()
        # Left unused past the clean hold.
        with freeze_time(now + timedelta(hours=72)):
            self.Equipment._cron_pharma_hold_expiry()
            self.assertEqual(machine.cleaning_state, 'hold_expired')
            self.assertIn('clean hold expired on', ' '.join(machine._pharma_fitness_issues()))
        self.assertIn('Clean hold expired', machine.message_ids[0].body)
        # Used, then left dirty past the dirty hold: the next cleaning is flagged.
        machine._pharma_register_use(self.tablet, now)
        self.env.flush_all()
        with freeze_time(now + timedelta(hours=10)):
            self.Equipment._cron_pharma_hold_expiry()
            self.assertEqual(machine.cleaning_state, 'dirty_hold_expired')
            self.assertIn('not clean', machine._pharma_fitness_issues(product=self.tablet))
            self.assertIn('not cleaned since', ' '.join(
                machine._pharma_fitness_issues(product=self.product)))
            second.with_user(self.operator).action_pharma_start()
        self.assertIn('Dirty hold expired', ' '.join(machine.message_ids.mapped('body')))
        self.assertTrue(second.dirty_hold_exceeded)
        self.assertIn('dirty hold ran out', second.message_ids[0].body)

    def test_dedicated_and_utility(self):
        """Dedicated equipment refuses another product; equipment without cleaning just records use."""
        machine = self.machine(product_dedicated=True)
        self.clean(machine)
        machine._pharma_register_use(self.tablet)
        self.assertEqual((machine.last_product_id, machine.cleaning_status), (self.tablet, 'dirty'))
        self.clean(machine)
        self.assertIn('dedicated to', ' '.join(machine._pharma_fitness_issues(product=self.product)))
        hvac = self.Equipment.create({'name': 'AHU', 'category_id': self.cat_utility.id})
        hvac._pharma_register_use(self.tablet)
        self.assertEqual((hvac.last_product_id, hvac.cleaning_state), (self.tablet, 'not_required'))
        self.complete(self.request(hvac, 'cleaning'))
        self.assertFalse(hvac.last_cleaning_request_id)

    def test_sterile(self):
        """A sterile category is sterilised after cleaning, until used or the hold ends."""
        self.enable_sterile()
        self.cat_mfg.sudo().pharma_sterile = True
        machine = self.machine()
        self.assertEqual((machine.sudo().sterilisation_required, machine.sudo().sterile_state),
                         (True, 'not_sterile'))
        self.assertTrue(machine._pharma_request_context('cleaning', 'Cleaning')['default_sterilisation_performed'])
        request = self.request(machine, sterilisation_performed=True)
        request.with_user(self.operator).action_pharma_start()
        request.work_done = 'Cleaned and autoclaved.'
        with self.assertRaises(UserError):
            request.with_user(self.operator).action_pharma_complete()
        request.sudo().sterilisation_method = 'steam'
        with self.assertRaises(UserError):
            request.with_user(self.operator).action_pharma_complete()
        request.sudo().write({'sterilisation_cycle_ref': 'AC-12', 'sterilisation_passed': True,
                              'sterile_hold_hours': 24})
        request.with_user(self.operator).action_pharma_complete()
        request.with_user(self.qa_only).action_qa_verify()
        machine = machine.sudo()
        self.assertEqual((machine.sterile_state, machine.last_sterilisation_request_id), ('sterile', request))
        self.assertEqual(self.request(machine).sudo().sterilisation_method, 'steam')
        self.assertFalse(machine._pharma_fitness_issues(product=self.tablet, sterile=True))
        self.env.flush_all()
        with freeze_time(fields.Datetime.now() + timedelta(hours=30)):
            self.Equipment._cron_pharma_hold_expiry()
            self.assertEqual(machine.sterile_state, 'hold_expired')
            self.assertIn('sterile hold expired', machine._pharma_fitness_issues(sterile=True))
        self.assertIn('Sterile hold expired', machine.message_ids[0].body)
        machine._pharma_register_use(self.tablet)
        self.assertIn('not sterile', machine._pharma_fitness_issues(sterile=True))
