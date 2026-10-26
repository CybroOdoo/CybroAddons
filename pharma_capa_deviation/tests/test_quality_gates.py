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
from odoo.tests import tagged

from odoo.addons.pharma_capa_deviation import post_init_hook, uninstall_hook

from .common import PharmaCapaCommon


@tagged('post_install', '-at_install')
class TestQualityGates(PharmaCapaCommon):
    """Deviations raised from IPQC and OOS, and the gates they hold."""

    def test_ipqc_failure_raises_deviation(self):
        """A failed IPQC check raises a linked deviation that gates the batch."""
        bmr = self.started_bmr()
        check = self.failed_ipqc(bmr)
        deviation = check.deviation_id
        self.assertEqual((deviation.batch_id, deviation.classification),
                         (bmr.production_id, 'major'))
        self.assertIn('IPQC Failure', deviation.description)
        self.assertEqual(bmr.deviation_count, 1)
        action = bmr.action_view_deviations()
        self.assertEqual(action['res_id'], deviation.id)
        with self.assertRaises(UserError):
            bmr._check_ipqc_failure_deviations()
        with self.assertRaises(UserError):
            bmr._check_open_deviations_capas()
        with self.assertRaises(UserError):
            bmr.step_ids._check_open_deviations_capas()
        # A second failure keeps the same deviation.
        check._on_ipqc_fail()
        self.assertEqual(check.deviation_id, deviation)
        deviation.with_user(self.qa_only).action_investigate()
        deviation.sudo().status = 'closed'
        with self.assertRaises(UserError):
            bmr._check_open_deviations_capas()
        with self.assertRaises(UserError):
            bmr.step_ids._check_open_deviations_capas()
        self.close_capa(deviation.capa_ids)
        bmr._check_open_deviations_capas()
        bmr.step_ids._check_open_deviations_capas()
        bmr._check_ipqc_failure_deviations()
        self.create_deviation(batch_id=bmr.production_id.id)
        self.assertEqual(len(bmr.action_view_deviations()['domain'][0][2]), 2)

    def test_ipqc_failure_without_deviation(self):
        """A failed IPQC check with no deviation blocks BMR completion."""
        bmr = self.started_bmr()
        check = self.failed_ipqc(bmr)
        check.deviation_id.sudo().unlink()
        with self.assertRaises(UserError):
            bmr._check_ipqc_failure_deviations()

    def test_oos_reject_raises_deviation(self):
        """QA rejecting an OOS investigation raises a critical QC deviation."""
        lot = self.create_lot(name='OOS-LOT')
        order = self.oos_order(lot)
        investigation = order.oos_investigation_ids.with_user(self.qa_only)
        investigation.action_escalate_to_phase_2()
        investigation.disposition = 'reject'
        investigation.action_close_investigation()
        deviation = order.deviation_ids
        self.assertEqual((deviation.classification, deviation.stage, deviation.lot_id),
                         ('critical', 'qc', lot))
        self.assertEqual(deviation.raised_by, self.qa_only)
        self.assertFalse(deviation.batch_id)
        self.assertIn('OOS Failure', deviation.description)
        self.assertEqual(order.deviation_count, 1)
        self.assertEqual(order.action_view_deviations()['res_model'], 'pharma.deviation')
        self.assertTrue(order._pharma_rejection_deferred())
        with self.assertRaises(ValidationError):
            order._check_qc_deviations_closed()
        deviation.with_user(self.qa_only).action_investigate()
        self.assertEqual(order.capa_ids, deviation.capa_ids)

    def test_oos_release_after_deviation(self):
        """Closing a released OOS deviation passes the QC order."""
        order = self.oos_order()
        investigation = order.oos_investigation_ids
        deviation = self.create_deviation(
            stage='qc', oos_investigation_id=investigation.id,
            qc_result_id=investigation.result_line_id.id)
        deviation.with_user(self.qa_only).action_investigate()
        self.close_capa(deviation.capa_ids)
        deviation.with_user(self.qa_only).disposition = 'release'
        deviation.with_user(self.qa_only).action_close()
        self.assertEqual(order.status, 'passed')
        order._check_qc_deviations_closed()

    def test_hooks(self):
        """The hooks rebuild the audit trail and purge mail records on uninstall."""
        deviation = self.create_deviation()
        deviation.message_post(body='Note')
        post_init_hook(self.env)
        uninstall_hook(self.env)
        self.assertFalse(self.env['mail.message'].search(
            [('model', '=', 'pharma.deviation'), ('res_id', '=', deviation.id)]))

    def test_roles_open_forms(self):
        """Operator and QA reviewer open the deviation, CAPA, BMR and QC order forms."""
        from lxml import etree
        bmr = self.started_bmr()
        deviation = self.failed_ipqc(bmr).deviation_id
        deviation.with_user(self.qa_only).action_investigate()
        order = self.oos_order()
        for user in (self.operator, self.qa_only):
            for record in (deviation, deviation.capa_ids, bmr, order):
                views = record.with_user(user).get_views([(False, 'form')])
                arch = etree.fromstring(views['views']['form']['arch'])
                fnames = {node.get('name') for node in arch.iter('field')
                          if not any(p.tag == 'list' for p in node.iterancestors())}
                record.with_user(user).read([f for f in fnames if f in record._fields])
