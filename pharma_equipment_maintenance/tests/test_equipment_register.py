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
from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, tagged
from odoo.tools import mute_logger

from odoo.addons.pharma_equipment_maintenance.hooks import post_init_hook

from .common import EquipmentCommon


@tagged('post_install', '-at_install')
class TestEquipmentRegister(EquipmentCommon):
    """Codes, classes and the GMP rules of the register."""

    def test_codes_and_names(self):
        """New equipment is numbered; codes are unique per company and lead the name."""
        first, second = self.instrument(), self.instrument(name='Balance 2')
        self.assertTrue(first.equipment_code.startswith('EQ-'))
        self.assertNotEqual(first.equipment_code, second.equipment_code)
        self.assertEqual(first.display_name, '[%s] Balance AB-220' % first.equipment_code)
        self.assertEqual(self.Equipment.name_search(first.equipment_code)[0][0], first.id)
        # A code entered by hand that the sequence has not reached yet is skipped.
        sequence = self.env.ref('pharma_equipment_maintenance.seq_pharma_equipment')
        manual = 'EQ-%04d' % sequence.number_next_actual
        self.instrument(name='Manual', equipment_code=manual)
        self.assertNotEqual(self.instrument(name='Balance 3').equipment_code, manual)
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'), self.env.cr.savepoint():
            self.instrument(name='Copy', equipment_code=first.equipment_code)
            self.env.flush_all()

    def test_class_and_gmp(self):
        """The category decides the class, the cleaning default and the GMP flag."""
        balance = self.instrument()
        self.assertEqual((balance.equipment_class, balance.cleaning_required, balance.gmp_critical),
                         ('testing', True, False))
        hvac = self.Equipment.create({'name': 'AHU 1', 'category_id': self.cat_utility.id})
        self.assertFalse(hvac.cleaning_required)
        machine = self.machine()
        self.assertTrue(machine.gmp_critical)
        with self.assertRaises(ValidationError):
            self.Equipment.create({'name': 'Loose', 'gmp_critical': True})
        with self.assertRaises(ValidationError):
            machine.write({'qualification_date': self.days(-1), 'requalification_date': self.days(-5)})
        form = Form(self.Equipment)
        form.name = 'From form'
        form.category_id = self.cat_mfg
        self.assertTrue(form.gmp_critical)
        form.category_id = self.cat_testing
        self.assertTrue(form.calibration_required)

    def test_qualification_records(self):
        """GMP critical equipment gets IQ, OQ and PQ; ticked stages carry over as passed."""
        machine = self.machine()
        self.assertEqual(sorted(machine.qualification_ids.mapped('stage')), ['iq', 'oq', 'pq'])
        self.assertEqual(machine.qualification_record_count, 3)
        self.assertEqual(machine.qualification_state, 'in_progress')
        self.assertEqual(set(machine.qualification_ids.mapped('state')), {'pending'})
        balance = self.instrument(iq_done=True, qualification_protocol_ref='PROT-7')
        self.assertFalse(balance.qualification_ids)
        balance.gmp_critical = True
        iq = balance.qualification_ids.filtered(lambda r: r.stage == 'iq')
        self.assertEqual((iq.state, iq.report_ref), ('passed', 'PROT-7'))
        self.assertEqual(iq.name, 'IQ - %s' % balance.display_name)
        action = balance.action_view_qualifications()
        self.assertEqual(action['domain'], [('equipment_id', '=', balance.id)])

    def sign(self, record, method='action_pass', **vals):
        """QA fills in the record and signs it."""
        record.with_user(self.qa_only).write(dict({
            'performed_on': self.days(-1), 'report_ref': 'RPT-%s' % record.stage}, **vals))
        getattr(record.with_user(self.qa_only), method)()

    def test_sign_off(self):
        """QA signs IQ, OQ, PQ in order; all passed qualifies the equipment."""
        machine = self.machine()
        iq, oq, pq = (machine.qualification_ids.filtered(lambda r, s=s: r.stage == s)
                      for s in ('iq', 'oq', 'pq'))
        with self.assertRaises(AccessError):
            iq.with_user(self.operator).action_pass()
        with self.assertRaises(UserError):
            iq.with_user(self.qa_only).action_pass()
        iq.with_user(self.qa_only).write({'performed_on': self.days(1), 'report_ref': 'RPT-iq'})
        with self.assertRaises(UserError):
            iq.with_user(self.qa_only).action_pass()
        iq.with_user(self.qa_only).write({'report_ref': False})
        iq.with_user(self.qa_only).write({'performed_on': self.days(-1)})
        with self.assertRaises(UserError):
            iq.with_user(self.qa_only).action_pass()
        with self.assertRaises(UserError):
            self.sign(oq)
        self.sign(iq)
        self.assertTrue(machine.iq_done)
        with self.assertRaises(UserError):
            iq.with_user(self.qa_only).action_pass()
        with self.assertRaises(UserError):
            iq.unlink()
        with self.assertRaises(UserError):
            self.sign(oq, 'action_fail')
        self.sign(oq, 'action_fail', notes='Speed out of range.')
        self.assertEqual((oq.state, machine.oq_done), ('failed', False))
        with self.assertRaises(UserError):
            iq.with_user(self.qa_only).action_reopen()
        oq.with_user(self.qa_only).action_reopen()
        self.assertEqual((oq.state, oq.signed_by.id), ('pending', False))
        self.sign(oq)
        self.sign(pq)
        self.assertEqual(machine.qualification_date, self.days(-1))
        self.assertEqual(machine.qualification_state, 'qualified')
        self.assertIn('PQ passed', machine.message_ids[0].body)
        archived = self.machine(name='Spare')
        record = archived.qualification_ids[:1]
        record.active = False
        with self.assertRaises(UserError):
            self.sign(record)

    def test_qualification_dates(self):
        """Due within the reminder window, expired once the date has passed."""
        machine = self.machine(iq_done=True, oq_done=True, pq_done=True,
                               qualification_date=self.days(-300))
        machine.requalification_date = self.days(200)
        self.assertEqual(machine.qualification_state, 'qualified')
        machine.requalification_date = self.days(30)
        self.assertEqual(machine.qualification_state, 'requalification_due')
        machine.requalification_date = self.days(-1)
        self.assertEqual(machine.qualification_state, 'expired')
        self.assertIn('qualification expired on', ' '.join(machine._pharma_fitness_issues()))
        machine.requalification_date = self.days(30)
        self.assertIn('requalification due on', ' '.join(machine._pharma_fitness_issues()))
        self.Equipment._cron_pharma_qualification_due()
        self.assertTrue(machine.activity_ids)
        self.Equipment._cron_pharma_qualification_due()
        self.assertEqual(len(machine.activity_ids), 1)
        hvac = self.Equipment.create({'name': 'AHU', 'category_id': self.cat_utility.id})
        self.assertEqual(hvac.qualification_state, 'not_required')

    def test_requalify(self):
        """QA requalifies qualified equipment now, keeping the interval."""
        machine = self.machine(iq_done=True, oq_done=True, pq_done=True,
                               qualification_date=self.days(-400))
        machine.requalification_date = self.days(-35)
        Wizard = self.env['pharma.equipment.requalify.wizard'].with_user(self.qa_only)
        wizard = Wizard.create({'equipment_id': machine.id, 'protocol_ref': 'RQ-1',
                                'reason': 'Moved to suite B after renovation.'})
        self.assertEqual(wizard.next_requalification_date, self.days(365))
        with self.assertRaises(AccessError):
            wizard.with_user(self.operator).action_requalify()
        wizard.reason = 'Moved'
        with self.assertRaises(UserError):
            wizard.action_requalify()
        wizard.reason = 'Moved to suite B after renovation.'
        wizard.requalified_on = self.days(1)
        with self.assertRaises(UserError):
            wizard.action_requalify()
        wizard.requalified_on = self.days(0)
        wizard.next_requalification_date = self.days(0)
        with self.assertRaises(UserError):
            wizard.action_requalify()
        wizard.next_requalification_date = self.days(365)
        wizard.action_requalify()
        self.assertEqual((machine.qualification_date, machine.requalification_date,
                          machine.qualification_protocol_ref, machine.qualification_state),
                         (self.days(0), self.days(365), 'RQ-1', 'qualified'))
        self.assertIn('Requalified on', machine.message_ids[0].body)
        new = self.machine(name='New one')
        wizard = Wizard.create({'equipment_id': new.id, 'protocol_ref': 'RQ-2',
                                'reason': 'Periodic requalification.'})
        self.assertEqual(wizard.next_requalification_date,
                         fields.Date.today() + relativedelta(years=1))
        with self.assertRaises(UserError):
            wizard.action_requalify()
        wizard.requalified_on = False
        self.assertFalse(wizard.next_requalification_date)

    def test_settings_and_hook(self):
        """Unknown check values fall back to block; the install hook numbers on."""
        self.set_check('nonsense')
        self.assertEqual(self.Equipment._pharma_equipment_settings(), {'check': 'block'})
        self.set_check('warn')
        self.assertEqual(self.Equipment._pharma_equipment_settings(), {'check': 'warn'})
        self.assertFalse(self.Equipment._pharma_sterile_enabled())
        self.enable_sterile()
        self.assertTrue(self.Equipment._pharma_sterile_enabled())
        balance = self.instrument()
        done_stage = self.env['maintenance.stage'].search([('done', '=', True)], limit=1)
        # A request closed before the module was installed: done stage, state New.
        old = self.Request.create({'name': 'Old repair', 'equipment_id': balance.id,
                                   'maintenance_type': 'corrective'})
        old.with_context(pharma_stage_sync=True).write({'stage_id': done_stage.id})
        self.env.flush_all()
        post_init_hook(self.env)
        old.invalidate_recordset(['pharma_state'])
        old.invalidate_recordset()
        self.assertEqual(old.pharma_state, 'qa_verified')
        sequence = self.env.ref('pharma_equipment_maintenance.seq_pharma_equipment')
        self.assertGreater(sequence.number_next_actual,
                           self.Equipment.with_context(active_test=False).search_count([]))
