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
from odoo.addons.pharmaceutical_base.tests.common import PharmaTestCommon


class PharmaTraceabilityCommon(PharmaTestCommon):
    """A lot-tracked finished product with an approved formula and FG specification."""

    @classmethod
    def setUpClass(cls):
        """Create the work centre, the tablets, their formula and FG specification."""
        super().setUpClass()
        cls.workcenter = cls.env['mrp.workcenter'].create({'name': 'Compression Suite'})
        cls.tablet_tmpl = cls.env['product.template'].create(
            {
                'name': 'Paracetamol Tablets',
                'is_storable': True,
                'tracking': 'lot',
            }
        )
        cls.tablet = cls.tablet_tmpl.product_variant_id
        fg_spec = cls.create_spec(cls.tablet_tmpl, 'finished')
        fg_spec.action_submit_review()
        fg_spec.with_user(cls.qa_user).action_approve()
        cls.bom = cls.env['mrp.bom'].create(
            {
                'product_tmpl_id': cls.tablet_tmpl.id,
                'product_qty': 1,
                'operation_ids': [(0, 0, {'name': 'Compress', 'workcenter_id': cls.workcenter.id})],
            }
        )
        cls.bom.with_user(cls.qa_user).action_approve_formula()

    def completed_mo(self, lot_name='FG-1', qty=10.0, produced=None):
        """A manufacturing order whose BMR is completed and whose FG lot has its QC order."""
        mo = self.env['mrp.production'].create(
            {
                'product_id': self.tablet.id,
                'bom_id': self.bom.id,
                'product_qty': qty,
            }
        )
        mo.action_confirm()
        mo.lot_producing_ids = self.create_lot(self.tablet, lot_name)
        bmr = mo.bmr_ids
        bmr.yield_actual = qty if produced is None else produced
        bmr.action_start()
        for step in bmr.step_ids:
            step.action_operator_sign()
            step.with_user(self.qa_user).action_supervisor_sign()
        if bmr.yield_flag:
            bmr.with_user(self.qa_user).action_qa_yield_signoff()
        bmr.with_user(self.qa_user).action_complete()
        return mo

    def fg_order(self, mo):
        """The finished-goods QC order of the order's lot."""
        return self.env['pharma.qc.test.order'].search(
            [('lot_id', 'in', mo.lot_producing_ids.ids), ('stage', '=', 'finished')]
        )

    def pass_order(self, order, value=100.0):
        """Enter a passing result and have QA approve the order."""
        order.action_start_test()
        order.result_line_ids.write({'actual_value': value})
        order.with_user(self.qa_user).action_approve()
        return order

    def eligible_mo(self, lot_name='FG-1'):
        """A completed order with a passed FG QC order, ready for QA release."""
        mo = self.completed_mo(lot_name)
        self.pass_order(self.fg_order(mo))
        return mo

    def queued_release(self, lot_name='FG-1'):
        """The QA release record of an eligible order, sent to the queue by QA."""
        mo = self.eligible_mo(lot_name)
        mo.with_user(self.qa_user).action_qa_release()
        return self.env['pharma.qa.release'].search([('production_id', '=', mo.id)])

    def create_deviation(self, **vals):
        """A deviation raised in manufacturing."""
        return self.env['pharma.deviation'].create(
            dict(
                {
                    'stage': 'manufacturing',
                    'classification': 'minor',
                    'description': 'Test deviation',
                },
                **vals,
            )
        )
