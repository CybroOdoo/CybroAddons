# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies
#    (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import QualityCommon


@tagged('post_install', '-at_install', 'quality_assurance')
class TestStockPicking(QualityCommon):

    # ------------------------------------------------------------------
    # Alert generation
    # ------------------------------------------------------------------
    def test_confirm_generates_alert_for_product_with_measures(self):
        picking = self._create_picking()
        picking.action_confirm()
        alerts = self._get_alerts(picking)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts.product_id, self.product)
        self.assertEqual(alerts.origin, picking.name)
        self.assertEqual(alerts.company_id, picking.company_id)
        self.assertTrue(alerts.name.startswith('QA'))

    def test_confirm_skips_product_without_measures(self):
        picking = self._create_picking(self.product_plain)
        picking.action_confirm()
        self.assertFalse(self._get_alerts(picking))

    def test_confirm_one_alert_per_move_with_measures(self):
        picking = self._create_picking(self.product | self.product_plain)
        picking.action_confirm()
        alerts = self._get_alerts(picking)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts.product_id, self.product)

    def test_confirm_skips_other_picking_types(self):
        picking = self._create_picking(picking_type=self.out_type)
        picking.action_confirm()
        self.assertFalse(self._get_alerts(picking))

    def test_confirm_twice_does_not_duplicate_alerts(self):
        picking = self._create_picking()
        picking.action_confirm()
        picking.invalidate_recordset(['alert_count', 'alert_ids'])
        picking.action_confirm()
        self.assertEqual(len(self._get_alerts(picking)), 1)

    # ------------------------------------------------------------------
    # Computed fields and smart button action
    # ------------------------------------------------------------------
    def test_alert_count_and_ids(self):
        picking = self._create_picking()
        self.assertEqual(picking.alert_count, 0)
        picking.action_confirm()
        picking.invalidate_recordset(['alert_count', 'alert_ids'])
        self.assertEqual(picking.alert_count, 1)
        self.assertEqual(picking.alert_ids, self._get_alerts(picking))

    def test_action_quality_alert_single_alert_opens_form(self):
        picking = self._create_picking()
        picking.action_confirm()
        picking.invalidate_recordset(['alert_count', 'alert_ids'])
        action = picking.action_quality_alert()
        self.assertEqual(action['res_model'], 'quality.alert')
        self.assertEqual(action['res_id'], self._get_alerts(picking).id)
        self.assertEqual(action['views'][0][1], 'form')
        self.assertEqual(action['context'], {})

    def test_action_quality_alert_multiple_alerts_uses_domain(self):
        self.env['quality.measure'].create({
            'name': 'Second Product Check',
            'product_id': self.product_plain.id,
            'picking_type_ids': [(6, 0, self.in_type.ids)],
        })
        picking = self._create_picking(self.product | self.product_plain)
        picking.action_confirm()
        picking.invalidate_recordset(['alert_count', 'alert_ids'])
        alerts = self._get_alerts(picking)
        self.assertEqual(len(alerts), 2)
        action = picking.action_quality_alert()
        for alert in alerts:
            self.assertIn(str(alert.id), action['domain'])

    # ------------------------------------------------------------------
    # Validation gate (_action_done)
    # ------------------------------------------------------------------
    def test_done_blocked_when_alert_is_waiting(self):
        picking = self._create_picking()
        self._make_ready(picking)
        self.assertEqual(self._get_alerts(picking).final_status, 'wait')
        with self.assertRaisesRegex(UserError, 'still in quality test'):
            picking._action_done()
        self.assertNotEqual(picking.state, 'done')

    def test_done_blocked_when_alert_failed(self):
        picking = self._create_picking()
        self._make_ready(picking)
        alert = self._get_alerts(picking)
        alert.action_generate_tests()
        self._fill_tests(alert, qty_result=99.0)
        with self.assertRaisesRegex(UserError, 'failed the quality test'):
            picking._action_done()
        self.assertNotEqual(picking.state, 'done')

    def test_done_succeeds_when_alert_passed(self):
        picking = self._create_picking()
        self._make_ready(picking)
        alert = self._get_alerts(picking)
        alert.action_generate_tests()
        self._fill_tests(alert)
        self.assertEqual(alert.final_status, 'pass')
        picking._action_done()
        self.assertEqual(picking.state, 'done')
        self.assertTrue(picking.date_done)

    def test_done_succeeds_without_quality_alerts(self):
        picking = self._create_picking(self.product_plain)
        self._make_ready(picking)
        picking._action_done()
        self.assertEqual(picking.state, 'done')
