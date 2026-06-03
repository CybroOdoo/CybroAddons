# -*- coding: utf-8 -*-

from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestMrpBomCosting(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.finished_product = cls.env['product.product'].create({
            'name': 'Costing Finished Product',
            'type': 'product',
            'uom_id': cls.uom_unit.id,
            'uom_po_id': cls.uom_unit.id,
        })
        cls.component = cls.env['product.product'].create({
            'name': 'Costing Component',
            'type': 'product',
            'uom_id': cls.uom_unit.id,
            'uom_po_id': cls.uom_unit.id,
            'list_price': 10.0,
        })
        cls.workcenter = cls.env['mrp.workcenter'].create({
            'name': 'Costing Work Center',
            'labour_cost': 2.0,
            'overhead_cost': 3.0,
        })

    def _set_costing_method(self, method):
        self.env['ir.config_parameter'].sudo().set_param(
            'manufacture_process_costing.process_costing_method', method)

    def _create_bom(self):
        return self.env['mrp.bom'].create({
            'product_tmpl_id': self.finished_product.product_tmpl_id.id,
            'product_qty': 1.0,
            'product_uom_id': self.uom_unit.id,
            'bom_line_ids': [
                Command.create({
                    'product_id': self.component.id,
                    'product_qty': 3.0,
                    'product_uom_id': self.uom_unit.id,
                }),
            ],
            'operation_ids': [
                Command.create({
                    'name': 'Assembly',
                    'workcenter_id': self.workcenter.id,
                    'time_cycle_manual': 15.0,
                }),
            ],
        })

    def test_onchange_bom_line_ids_creates_material_costs(self):
        bom = self._create_bom()

        bom._onchange_bom_line_ids()

        self.assertEqual(len(bom.material_cost_ids), 1)
        material = bom.material_cost_ids
        self.assertEqual(material.product_id, self.component)
        self.assertAlmostEqual(material.planned_qty, 3.0)
        self.assertEqual(material.uom_id, self.uom_unit)
        self.assertAlmostEqual(material.cost_unit, 10.0)
        self.assertAlmostEqual(bom.total_material_cost, 30.0)

    def test_onchange_operation_ids_uses_workcenter_costs(self):
        self._set_costing_method('work-center')
        bom = self._create_bom()

        bom._onchange_operation_ids()

        self.assertEqual(len(bom.labour_cost_ids), 1)
        self.assertEqual(len(bom.overhead_cost_ids), 1)
        self.assertAlmostEqual(bom.labour_cost_ids.cost_minute, 2.0)
        self.assertAlmostEqual(bom.overhead_cost_ids.cost_minute, 3.0)
        self.assertAlmostEqual(bom.total_labour_cost, 30.0)
        self.assertAlmostEqual(bom.total_overhead_cost, 45.0)

    def test_onchange_operation_ids_manual_costing_keeps_costs_empty(self):
        self._set_costing_method('manually')
        bom = self._create_bom()

        bom._onchange_operation_ids()

        self.assertEqual(len(bom.labour_cost_ids), 1)
        self.assertEqual(len(bom.overhead_cost_ids), 1)
        self.assertEqual(bom.labour_cost_ids.cost_minute, 0.0)
        self.assertEqual(bom.overhead_cost_ids.cost_minute, 0.0)
