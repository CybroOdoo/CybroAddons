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
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import PharmaTraceabilityCommon


@tagged('post_install', '-at_install')
class TestCoa(PharmaTraceabilityCommon):
    """Certificates of Analysis: content, locking and the PDF."""

    def setUp(self):
        """Release one batch to obtain its CoA."""
        super().setUp()
        self.release = self.queued_release()
        self.release.with_user(self.qa_user).action_confirm()
        self.coa = self.release.coa_id

    def test_content(self):
        """The CoA gathers the batch QC results, deviations and CAPAs."""
        coa = self.coa
        self.assertTrue(coa.name.startswith('COA/'))
        self.assertEqual(coa.qc_test_ids, self.fg_order(self.release.production_id))
        self.assertEqual(coa.qc_result_ids, coa.qc_test_ids.result_line_ids)
        self.assertFalse(coa.oos_ids or coa.ipqc_ids)
        deviation = self.create_deviation(batch_id=coa.batch_id.id)
        capa = self.env['pharma.capa'].create(
            {
                'deviation_id': deviation.id,
                'capa_type': 'corrective',
                'assigned_to': self.qa_user.id,
            }
        )
        coa.invalidate_recordset()
        self.assertEqual((coa.deviation_ids, coa.capa_ids), (deviation, capa))
        self.assertEqual((coa.deviation_count, coa.capa_count), (1, 1))
        self.assertEqual(coa._get_report_deviations(), deviation)
        self.assertEqual(coa._get_report_capas(), capa)
        self.assertEqual(coa.action_view_coa_deviations()['domain'], [('id', 'in', deviation.ids)])
        self.assertEqual(coa.action_view_coa_capas()['domain'], [('id', 'in', capa.ids)])

    def test_unlinked_coa(self):
        """A CoA without batch or lot lists no quality records."""
        coa = self.env['pharma.coa'].create({})
        self.assertFalse(coa.qc_test_ids or coa.deviation_ids or coa.ipqc_ids)
        coa.write({'released_by': self.qa_user.id})
        coa.unlink()

    def test_unlinked_coa_ignores_unrelated_deviations(self):
        """A CoA without batch or lot does not pick up deviations that have none either."""
        self.create_deviation()
        coa = self.env['pharma.coa'].create({})
        self.assertFalse(coa.deviation_ids or coa.capa_ids)
        self.assertEqual((coa.deviation_count, coa.capa_count), (0, 0))

    def test_locked(self):
        """A released CoA can be neither edited nor deleted."""
        with self.assertRaises(ValidationError):
            self.coa.write({'released_by': self.operator.id})
        with self.assertRaises(ValidationError):
            self.coa.unlink()
        self.coa.message_post(body='Followers may still discuss it.')

    def test_report(self):
        """The CoA prints."""
        html, _fmt = self.env['ir.actions.report']._render_qweb_html(
            'pharma_traceability_coa.action_report_pharma_coa', self.coa.ids
        )
        self.assertIn(self.coa.name, html.decode())
