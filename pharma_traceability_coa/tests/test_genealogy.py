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
from odoo.tests import tagged

from .common import PharmaTraceabilityCommon


@tagged('post_install', '-at_install')
class TestGenealogy(PharmaTraceabilityCommon):
    """Backward and forward traceability of a lot."""

    def test_genealogy(self):
        """A released lot traces back to its order, BMR, QC and CoA."""
        release = self.queued_release()
        release.with_user(self.qa_user).action_confirm()
        lot = release.lot_id
        mo = release.production_id
        self.assertEqual(lot.produced_production_ids, mo)
        self.assertEqual(lot.bmr_ids, mo.bmr_ids)
        self.assertEqual(lot.qc_test_ids, self.fg_order(mo))
        self.assertEqual(lot.fg_qc_ids, self.fg_order(mo))
        self.assertFalse(lot.incoming_qc_ids or lot.ipqc_ids)
        self.assertEqual(lot.coa_ids, release.coa_id)
        self.assertFalse(lot.delivery_order_ids or lot.customer_ids or lot.invoice_ids)

    def test_raw_material_quality(self):
        """Raw-material deviations (lot only, no batch) appear on the finished lot."""
        raw_lot = self.create_lot(name='RM-1')
        self.pass_order(self.create_order(lot=raw_lot))
        self.bom.sudo().bom_line_ids = [(0, 0, {'product_id': self.product.id, 'product_qty': 1})]
        mo = self.eligible_mo()
        lot = mo.lot_producing_ids
        self.assertIn(raw_lot, lot.consumed_lot_ids)
        deviation = self.create_deviation(lot_id=raw_lot.id, stage='qc')
        capa = self.env['pharma.capa'].create(
            {
                'deviation_id': deviation.id,
                'capa_type': 'corrective',
                'assigned_to': self.qa_user.id,
            }
        )
        lot.invalidate_recordset()
        self.assertEqual((lot.deviation_ids, lot.capa_ids), (deviation, capa))
        self.assertEqual((lot.deviation_count, lot.capa_count), (1, 1))
        self.assertEqual(lot.action_view_lot_deviations()['domain'], [('id', 'in', deviation.ids)])
        self.assertEqual(lot.action_view_lot_capas()['domain'], [('id', 'in', capa.ids)])

    def test_unproduced_lot(self):
        """A lot that was never produced has no genealogy."""
        lot = self.create_lot(name='LOOSE')
        self.assertFalse(lot.produced_production_ids or lot.consumed_lot_ids)
        self.assertFalse(lot.purchase_order_ids or lot.vendor_ids)
