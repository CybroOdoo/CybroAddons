# -*- coding: utf-8 -*-

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductProduct(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Kanban Finished Product',
            'type': 'consu',
        })
        cls.component = cls.env['product.product'].create({
            'name': 'Kanban Component',
            'type': 'consu',
        })
        cls.workcenter = cls.env['mrp.workcenter'].create({
            'name': 'Kanban Workcenter',
        })
        cls.bom = cls.env['mrp.bom'].create({
            'product_id': cls.product.id,
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'product_qty': 1.0,
            'product_uom_id': cls.product.uom_id.id,
            'type': 'normal',
            'bom_line_ids': [
                Command.create({
                    'product_id': cls.component.id,
                    'product_qty': 1.0,
                    'product_uom_id': cls.component.uom_id.id,
                }),
            ],
        })
        cls.production = cls.env['mrp.production'].create({
            'product_id': cls.product.id,
            'product_uom_id': cls.product.uom_id.id,
            'bom_id': cls.bom.id,
            'product_qty': 1.0,
        })
        cls.workorder = cls.env['mrp.workorder'].create({
            'name': 'Kanban Work Order',
            'workcenter_id': cls.workcenter.id,
            'product_uom_id': cls.product.uom_id.id,
            'production_id': cls.production.id,
            'duration_expected': 1.0,
        })

    def _assert_action(self, action, name, res_model, domain):
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['name'], name)
        self.assertEqual(action['view_mode'], 'list,form')
        self.assertEqual(action['res_model'], res_model)
        self.assertEqual(action['domain'], domain)
        self.assertEqual(action['context'], "{'create': False}")

    def test_action_mrp_orders_returns_product_manufacturing_orders(self):
        self._assert_action(
            self.product.action_mrp_orders(),
            'Manufacturing Orders',
            'mrp.production',
            [('product_id', '=', self.product.id)],
        )

    def test_action_work_orders_returns_product_work_orders(self):
        self._assert_action(
            self.product.action_work_orders(),
            'WorkOrders',
            'mrp.workorder',
            [('product_id', '=', self.product.id)],
        )

    def test_action_un_build_orders_returns_product_unbuild_orders(self):
        self._assert_action(
            self.product.action_un_build_orders(),
            'Unbuild Orders',
            'mrp.unbuild',
            [('product_id', '=', self.product.id)],
        )

    def test_action_scrap_orders_returns_product_scrap_orders(self):
        self._assert_action(
            self.product.action_scrap_orders(),
            'Scrap Orders',
            'stock.scrap',
            [('product_id', '=', self.product.id)],
        )

    def test_action_bom_returns_template_boms(self):
        self._assert_action(
            self.product.action_bom(),
            'BOM',
            'mrp.bom',
            [('product_tmpl_id', '=', self.product.product_tmpl_id.id)],
        )

    def test_compute_mrp_count_counts_product_manufacturing_orders(self):
        self.product._compute_mrp_count()

        self.assertEqual(self.product.mrp_count, 1)

    def test_compute_work_count_counts_product_work_orders(self):
        self.product._compute_work_count()

        self.assertEqual(self.product.work_count, 1)

    def test_compute_bom_count_counts_template_boms(self):
        self.product._compute_bom_count()

        self.assertEqual(self.product.bom_count, 1)
