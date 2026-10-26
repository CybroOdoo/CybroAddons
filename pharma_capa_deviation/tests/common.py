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
from odoo.tests import Form

from odoo.addons.pharmaceutical_base.tests.common import PharmaTestCommon


class PharmaCapaCommon(PharmaTestCommon):
    """Role users, a finished product with an approved formula and helpers."""

    @classmethod
    def setUpClass(cls):
        """Add a QA-only reviewer and the finished product with its formula."""
        super().setUpClass()
        ref = cls.env.ref
        # QA is a review role and does not inherit the User role's create rights.
        cls.qa_only = cls.env['res.users'].create({
            'name': 'QA Reviewer', 'login': 'pharma_test_qa_only',
            'group_ids': [(4, ref('pharmaceutical_base.group_pharma_role_qa').id),
                          (4, ref('mrp.group_mrp_user').id),
                          (4, ref('stock.group_stock_user').id)],
        })
        cls.workcenter = cls.env['mrp.workcenter'].create({'name': 'Blending Suite'})
        cls.tablet_tmpl = cls.env['product.template'].create({
            'name': 'Ibuprofen Tablets', 'is_storable': True,
        })
        cls.tablet = cls.tablet_tmpl.product_variant_id
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.tablet_tmpl.id,
            'product_qty': 1,
            'operation_ids': [(0, 0, {'name': 'Blend', 'workcenter_id': cls.workcenter.id})],
        })
        cls.bom.with_user(cls.qa_user).sudo().action_approve_formula()
        cls.ipqc_spec = cls.create_spec(cls.tablet_tmpl, 'ipqc', 1.0, 5.0)

    def started_bmr(self):
        """A confirmed order whose BMR has started, with IPQC enabled."""
        mo = self.env['mrp.production'].create({
            'product_id': self.tablet.id, 'bom_id': self.bom.id, 'product_qty': 5,
        })
        mo.action_confirm()
        bmr = mo.bmr_ids
        bmr.write({'enable_ipqc': True})
        bmr.action_start()
        return bmr

    def failed_ipqc(self, bmr):
        """Sign the first step and record a failing IPQC check on it."""
        step = bmr.step_ids[0]
        step.action_operator_sign()
        form = Form(self.env['pharma.ipqc.result'])
        form.bmr_id = bmr
        form.step_id = step
        form.parameter_id = self.ipqc_spec.parameter_ids
        check = form.save()
        check.write({'actual_value': 9.0})
        check.action_sign()
        return check

    def create_deviation(self, user=None, **vals):
        """A deviation raised by ``user`` (the operator by default)."""
        return self.env['pharma.deviation'].with_user(user or self.operator).create(dict({
            'stage': 'manufacturing', 'classification': 'major', 'description': 'Spill at weighing',
        }, **vals))

    def investigated(self, **vals):
        """A deviation under investigation, with its auto-raised CAPA."""
        deviation = self.create_deviation(**vals)
        deviation.with_user(self.qa_only).action_investigate()
        return deviation

    def close_capa(self, capa):
        """Run a corrective CAPA through to closed as QA."""
        capa = capa.with_user(self.qa_only)
        capa.write({'action_plan': 'Retrain operators', 'effectiveness_conclusion': 'No recurrence',
                    'root_cause': capa.root_cause or 'Worn seal'})
        capa.action_start()
        capa.action_verify()
        capa.action_close()
        return capa

    def oos_order(self, lot=None):
        """A QC test order in progress whose result is out of specification."""
        order = self.create_order(lot=lot)
        order.action_start_test()
        order.result_line_ids.write({'actual_value': 90.0})
        return order
