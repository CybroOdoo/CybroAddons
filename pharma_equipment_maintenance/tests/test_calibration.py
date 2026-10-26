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
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import EquipmentCommon


@tagged('post_install', '-at_install')
class TestCalibration(EquipmentCommon):
    """Calibration records from the work to QA release."""

    def test_points(self):
        """Each point is compared with its tolerance; the points decide the outcome."""
        result = self.calibration(self.instrument(), as_found=100.6, as_left=100.2)
        point = result.point_ids
        self.assertAlmostEqual(point.as_found_deviation, 0.6)
        self.assertEqual((point.as_found_result, point.as_left_result), ('fail', 'pass'))
        self.assertEqual((result.calibration_as_found_result, result.calibration_as_left_result,
                          result.calibration_passed), ('fail', 'pass', True))
        with self.assertRaises(ValidationError):
            point.tolerance = 0.0
        empty = self.Calibration.create({'equipment_id': self.instrument(name='B2').id})
        self.assertEqual((empty.calibration_passed, empty.calibration_as_found_result), (False, False))
        self.assertNotEqual(empty.name, 'New')

    def test_workflow_gates(self):
        """Start, complete and verify only from the right state, by the right people."""
        balance = self.instrument()
        result = self.Calibration.with_user(self.operator).create({'equipment_id': balance.id})
        with self.assertRaises(UserError):
            result.action_complete()
        result.action_start()
        with self.assertRaises(UserError):
            result.action_start()
        with self.assertRaises(UserError):
            result.action_complete()
        self.env['pharma.calibration.point'].with_user(self.operator).create({
            'result_id': result.id, 'nominal_value': 10.0, 'as_found': 10.0,
            'as_left': 10.0, 'tolerance': 0.1})
        with self.assertRaises(UserError):
            result.action_complete()
        result.certificate_number = 'C-9'
        with self.assertRaises(UserError):
            result.with_user(self.qa_only).action_qa_verify()
        result.action_complete()
        self.assertEqual((result.state, result.completed_by), ('completed', self.operator))
        with self.assertRaises(UserError):
            result.action_complete()
        with self.assertRaises(AccessError):
            result.with_user(self.operator).action_qa_verify()
        # The QA reviewer who completed it cannot verify it.
        own = self.Calibration.with_user(self.qa_user).create({
            'equipment_id': balance.id, 'certificate_number': 'C-10',
            'point_ids': [(0, 0, {'nominal_value': 1.0, 'as_found': 1.0, 'as_left': 1.0,
                                  'tolerance': 0.1})]})
        own.action_start()
        own.action_complete()
        with self.assertRaises(UserError):
            own.with_user(self.qa_user).action_qa_verify()
        with self.assertRaises(ValidationError):
            self.Calibration.create({'equipment_id': balance.id,
                                     'calibration_performed_on': self.days(1)})
        with self.assertRaises(ValidationError):
            self.Calibration.create({'equipment_id': balance.id, 'calibration_frequency_days': 0})
        with self.assertRaises(ValidationError):
            self.Calibration.create({'equipment_id': balance.id, 'calibration_reminder_days': -1})

    def test_pass(self):
        """A verified pass calibrates the instrument and locks the record."""
        balance = self.instrument()
        self.assertEqual(balance.calibration_state, 'overdue')
        self.assertIn('out of calibration', balance._pharma_fitness_issues())
        result = self.calibrate(balance, calibration_frequency_days=180, calibration_reminder_days=20)
        self.assertEqual(result.state, 'qa_verified')
        self.assertEqual((balance.last_calibration_result_id, balance.last_calibration_date,
                          balance.next_calibration_date, balance.calibration_state),
                         (result, self.days(0), self.days(180), 'ok'))
        self.assertIn('Calibration passed', balance.message_ids[0].body)
        with self.assertRaises(UserError):
            result.with_user(self.qa_only).action_qa_verify()
        with self.assertRaises(UserError):
            result.notes = 'Changed later'
        with self.assertRaises(UserError):
            result.point_ids.as_left = 99.0
        with self.assertRaises(UserError):
            result.point_ids.unlink()
        with self.assertRaises(UserError):
            self.env['pharma.calibration.point'].create({
                'result_id': result.id, 'nominal_value': 1.0, 'as_found': 1.0,
                'as_left': 1.0, 'tolerance': 0.1})
        with self.assertRaises(UserError):
            result.unlink()
        # The next calibration carries the interval and reminder over.
        follow_up = self.Calibration.create({'equipment_id': balance.id})
        self.assertEqual((follow_up.calibration_frequency_days, follow_up.calibration_reminder_days),
                         (180, 20))
        follow_up.unlink()
        # Due soon inside the reminder window; the cron reminds once.
        short = self.instrument(name='Short interval')
        self.calibrate(short, calibration_frequency_days=10, calibration_reminder_days=20)
        self.assertEqual(short.calibration_state, 'due_soon')
        self.Equipment._cron_pharma_calibration_due()
        self.Equipment._cron_pharma_calibration_due()
        self.assertEqual(len(short.activity_ids), 1)
        self.assertEqual(balance.action_view_calibrations()['domain'], [('equipment_id', '=', balance.id)])
        self.assertEqual(balance.action_raise_calibration()['context'], {'default_equipment_id': balance.id})

    def test_fail_and_impact(self):
        """A failed calibration puts the instrument out; an as-found failure flags earlier results."""
        balance = self.fit_instrument()
        failed = self.calibration(balance, as_found=101.0, as_left=101.0)
        failed.action_complete()
        action = failed.with_user(self.qa_only).action_qa_verify()
        self.assertEqual(action['res_model'], 'pharma.qc.result.line')
        self.assertEqual((balance.calibration_failed_on, balance.calibration_state),
                         (self.days(0), 'overdue'))
        self.assertEqual(failed.impact_reference_date, self.days(0))
        self.assertTrue(failed.activity_ids)
        self.assertIn('FAILED', ' '.join(balance.message_ids.mapped('body')))
        self.assertIn('Calibration Impact', failed.action_calibration_impact_assessment()['name'])
        self.Equipment._cron_pharma_calibration_due()
        # A later pass brings it back.
        self.calibrate(balance)
        self.assertEqual((balance.calibration_failed_on, balance.calibration_state), (False, 'ok'))
        # As-found failure on a never-calibrated instrument: every result is suspect.
        fresh = self.instrument(name='Fresh')
        first = self.calibration(fresh, as_found=101.0, as_left=100.0)
        first.action_complete()
        first.with_user(self.qa_only).action_qa_verify()
        self.assertFalse(first.impact_reference_date)
        self.assertIn('no earlier calibration', first.action_calibration_impact_assessment()['name'])
