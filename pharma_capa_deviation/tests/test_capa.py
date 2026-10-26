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
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from .common import PharmaCapaCommon


@tagged('post_install', '-at_install')
class TestCapa(PharmaCapaCommon):
    """CAPA life cycle, root cause and the preventive plan preview."""

    def test_life_cycle(self):
        """Open, in progress, verified, closed — each step checked."""
        deviation = self.investigated(root_cause='Worn seal')
        capa = deviation.capa_ids.with_user(self.qa_only)
        self.assertTrue(capa.name.startswith('CAPA') or capa.name != 'New')
        self.assertEqual(capa.root_cause, 'Worn seal')
        self.assertEqual(capa.deviation_count, 1)
        self.assertEqual(capa.action_view_deviation()['res_id'], deviation.id)
        with self.assertRaises(UserError):
            capa.with_user(self.operator).action_start()
        with self.assertRaises(UserError):
            capa.action_verify()
        with self.assertRaises(UserError):
            capa.action_close()
        capa.action_start()
        self.assertEqual(capa.status, 'in_progress')
        with self.assertRaises(UserError):
            capa.action_start()
        with self.assertRaises(UserError):
            capa.action_verify()
        capa.effectiveness_conclusion = 'No recurrence in 3 batches'
        capa.action_verify()
        with self.assertRaises(UserError):
            capa.action_close()
        capa.action_plan = 'Replace seals monthly'
        capa.action_close()
        self.assertEqual((capa.status, capa.closed_by), ('closed', self.qa_only))
        with self.assertRaises(UserError):
            capa.status = 'open'

    def test_close_needs_root_cause(self):
        """A CAPA without a root cause cannot close."""
        capa = self.investigated().capa_ids.with_user(self.qa_only)
        capa.write({'action_plan': 'Plan', 'effectiveness_conclusion': 'OK'})
        capa.action_start()
        capa.action_verify()
        with self.assertRaises(UserError):
            capa.action_close()

    def test_root_cause_override(self):
        """Editing the root cause overrides the deviation's; clearing follows it again."""
        deviation = self.investigated(root_cause='Worn seal')
        capa = deviation.capa_ids.with_user(self.qa_only)
        capa.root_cause = 'Operator error'
        self.assertTrue(capa.root_cause_overridden)
        deviation.sudo().root_cause = 'Worn gasket'
        self.assertEqual(capa.root_cause, 'Operator error')
        capa.root_cause = ''
        self.assertFalse(capa.root_cause_overridden)
        self.assertEqual(capa.root_cause, 'Worn gasket')
        capa.root_cause = 'Something else'
        capa.action_follow_deviation_root_cause()
        self.assertEqual(capa.root_cause, 'Worn gasket')

    def test_preventive_without_addon(self):
        """A preventive CAPA starts on its action plan after the add-on dialog."""
        capa = self.investigated().capa_ids.with_user(self.qa_only)
        capa.capa_type = 'preventive'
        self.assertTrue(capa.preventive_premium_locked)
        self.assertFalse(capa.preventive_managed)
        self.assertIn('No recurring checks', capa.effectiveness_check)
        action = capa.action_start()
        self.assertEqual(action['context']['pharma_capa_start_ids'], capa.ids)
        self.assertEqual(capa.status, 'open')
        self.assertTrue(capa.action_open_preventive_feature())
        feature = self.env.ref('pharma_capa_deviation.pharma_premium_feature_capa_preventive')
        feature.with_user(self.qa_only).with_context(
            pharma_capa_start_ids=capa.ids).action_start_capa_with_action_plan()
        self.assertEqual(capa.status, 'in_progress')

    def test_plan_summaries(self):
        """Scope and schedule read as one line for each kind of plan."""
        capa = self.investigated().capa_ids.sudo()
        self.assertFalse(capa.scope_summary or capa.plan_summary)
        capa.capa_type = 'preventive'
        self.assertTrue(capa.scope_site_wide)
        self.assertIn('Site-wide', capa.scope_summary)
        self.assertIn('not yet scheduled', capa.plan_summary)
        location = self.env['stock.warehouse'].search([], limit=1).lot_stock_id
        capa.write({
            'scope_product_ids': [(6, 0, self.tablet_tmpl.ids)],
            'scope_workcenter_ids': [(6, 0, self.workcenter.ids)],
            'scope_location_ids': [(6, 0, location.ids)],
            'trigger_type': 'batch', 'control_nature': 'campaign', 'cycle_count': 5,
        })
        self.assertFalse(capa.scope_site_wide)
        self.assertIn('Ibuprofen Tablets', capa.scope_summary)
        self.assertIn('Blending Suite', capa.scope_summary)
        self.assertIn('next 5 completed test(s)', capa.plan_summary)
        capa.write({'scope_product_ids': [(5,)], 'trigger_type': 'time',
                    'interval_count': 3, 'interval_uom': 'month'})
        self.assertIn('on any material', capa.scope_summary)
        self.assertIn('every 3 Months, 5 time(s)', capa.plan_summary)
        capa.control_nature = 'permanent'
        self.assertIn('every 3 Months (', capa.plan_summary)
        capa.trigger_type = False
        self.assertEqual(capa._schedule_summary(), '')
        with self.assertRaises(ValidationError):
            capa.write({'trigger_type': 'batch', 'control_nature': 'permanent'})

    def test_onchanges(self):
        """Without the add-on the preventive plan fields are cleared; a test trigger is a campaign."""
        capa = self.investigated().capa_ids
        with Form(capa.sudo()) as form:
            form.capa_type = 'preventive'
            self.assertFalse(form.trigger_type)
        capa = capa.sudo()
        capa.trigger_type = 'batch'
        capa._onchange_trigger_type()
        self.assertEqual((capa.control_nature, capa.cycle_count), ('campaign', 5))
        capa.trigger_type = 'time'
        capa._onchange_trigger_type()
        self.assertEqual(capa.cycle_count, 2)
        capa.preventive_managed = True
        capa.scope_product_ids = False
        capa.trigger_type = False
        capa.control_nature = False
        capa._onchange_capa_type()
        self.assertEqual(capa.trigger_type, 'time')
        self.assertEqual(capa.control_nature, 'campaign')
