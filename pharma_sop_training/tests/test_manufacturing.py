# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import PharmaSopCommon


@tagged('post_install', '-at_install')
class TestSopManufacturing(PharmaSopCommon):
    """SOPs on routing operations, formula approval and BMR sign-off."""

    @classmethod
    def setUpClass(cls):
        """Effective SOPs on two work centres and a finished product."""
        super().setUpClass()
        cls.sop = cls.effective_sop()
        cls.coating_sop = cls.effective_sop('Coating', cls.other_workcenter)
        cls.tablet_tmpl = cls.env['product.template'].create({
            'name': 'Paracetamol Tablets', 'is_storable': True,
        })

    def create_bom(self, sop=None):
        """A one-operation formula whose operation follows ``sop``."""
        return self.env['mrp.bom'].create({
            'product_tmpl_id': self.tablet_tmpl.id,
            'product_qty': 1,
            'operation_ids': [(0, 0, {
                'name': 'Granulate', 'sequence': 10,
                'workcenter_id': self.workcenter.id, 'sop_id': (sop or self.sop).id,
            })],
        })

    def test_allowed_sops(self):
        """Only Effective SOPs of the operation's work centre can be picked."""
        operation = self.create_bom().operation_ids
        self.assertEqual(operation.allowed_sop_ids, self.sop)
        draft = self.env['mrp.routing.workcenter'].new({'name': 'Loose'})
        self.assertFalse(draft.allowed_sop_ids)
        draft.sop_id = self.sop
        draft._onchange_sop_id_set_workcenter()
        self.assertEqual(draft.workcenter_id, self.workcenter)
        draft.workcenter_id = self.other_workcenter
        draft._onchange_workcenter_id_clear_sop()
        self.assertFalse(draft.sop_id)

    def test_operation_sop_checks(self):
        """The SOP must be Effective and belong to the operation's work centre."""
        operation = self.create_bom().operation_ids
        with self.assertRaises(ValidationError):
            operation.sop_id = self.coating_sop
        draft = self.create_sop('Milling')
        with self.assertRaises(ValidationError):
            operation.sop_id = draft

    def test_formula_needs_effective_sop(self):
        """An operation may lack an SOP until its formula is approved, which
        needs an Effective SOP on every operation."""
        bom = self.create_bom()
        self.sop.with_user(self.qa_user).action_archive_sop()
        with self.assertRaises(ValidationError):
            bom.with_user(self.qa_user).action_approve_formula()
        bom.operation_ids.sop_id = False
        with self.assertRaises(ValidationError):
            bom.with_user(self.qa_user).action_approve_formula()

    def test_bmr_step_sop_and_signoff(self):
        """The BMR step takes the operation's SOP; sign-off needs passed training."""
        bom = self.create_bom()
        bom.with_user(self.qa_user).action_approve_formula()
        mo = self.env['mrp.production'].create({
            'product_id': self.tablet_tmpl.product_variant_id.id,
            'bom_id': bom.id, 'product_qty': 5,
        })
        mo.action_confirm()
        bmr = mo.bmr_ids
        step = bmr.step_ids
        self.assertEqual(step.sop_id, self.sop)
        bmr.action_start()
        with self.assertRaises(ValidationError):
            step.with_user(self.operator).action_operator_sign()
        self.pass_training(self.training_of(self.sop))
        step.with_user(self.operator).action_operator_sign()
        self.assertEqual(step.operator_id, self.operator)

