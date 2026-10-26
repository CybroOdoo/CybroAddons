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
from odoo.tests import TransactionCase


class PharmaTestCommon(TransactionCase):
    """Shared users, products and helpers for the pharmaceutical base tests."""

    @classmethod
    def setUpClass(cls):
        """Create the role users, a lot-tracked product and an approved specification."""
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True,
                                       mail_create_nolog=True, no_reset_password=True))
        ref = cls.env.ref
        stock_mrp = [(4, ref('mrp.group_mrp_user').id), (4, ref('stock.group_stock_user').id)]
        cls.operator = cls.env['res.users'].create({
            'name': 'Pharma Operator', 'login': 'pharma_test_operator',
            'group_ids': [(4, ref('pharmaceutical_base.group_pharma_role_user').id)] + stock_mrp,
        })
        cls.qa_user = cls.env['res.users'].create({
            'name': 'Pharma QA', 'login': 'pharma_test_qa',
            'group_ids': [(4, ref('pharmaceutical_base.group_pharma_role_qa').id),
                          (4, ref('pharmaceutical_base.group_pharma_role_user').id)] + stock_mrp,
        })
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Paracetamol API', 'is_storable': True, 'tracking': 'lot',
        })
        cls.product = cls.product_tmpl.product_variant_id
        cls.spec = cls.create_spec(cls.product_tmpl, 'incoming')
        cls.spec.action_submit_review()
        cls.spec.with_user(cls.qa_user).action_approve()

    @classmethod
    def create_spec(cls, template, stage, min_value=98.0, max_value=102.0):
        """Create a draft specification with one Assay parameter."""
        return cls.env['pharma.qc.spec'].create({
            'product_id': template.id,
            'stage': stage,
            'parameter_ids': [(0, 0, {
                'parameter_name': 'Assay', 'min_value': min_value, 'max_value': max_value,
            })],
        })

    def create_lot(self, product=None, name='LOT-1'):
        """Create a lot of ``product`` (the API by default)."""
        return self.env['stock.lot'].create({
            'name': name, 'product_id': (product or self.product).id,
        })

    def create_order(self, lot=None, stage='incoming', template=None):
        """Create a QC test order; its result lines come from the approved spec."""
        return self.env['pharma.qc.test.order'].create({
            'product_id': (template or self.product_tmpl).id,
            'lot_id': (lot or self.create_lot()).id,
            'stage': stage,
        })
