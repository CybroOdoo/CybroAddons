# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestMrpProductionCosting(TransactionCase):

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

    def _prepare_bom_costs(self):
        self._set_costing_method('work-center')
        bom = self._create_bom()
        bom._onchange_bom_line_ids()
        bom._onchange_operation_ids()
        return bom

    def _create_production(self, bom=None):
        bom = bom or self._prepare_bom_costs()
        production = self.env['mrp.production'].create({
            'product_id': self.finished_product.id,
            'product_qty': 1.0,
            'product_uom_id': self.uom_unit.id,
            'bom_id': bom.id,
        })
        production._onchange_bom_id()
        return production

    def test_onchange_bom_id_copies_cost_lines_and_totals(self):
        bom = self._prepare_bom_costs()
        production = self._create_production(bom)

        self.assertEqual(len(production.material_cost_ids), 1)
        self.assertEqual(len(production.labour_cost_ids), 1)
        self.assertEqual(len(production.overhead_cost_ids), 1)
        self.assertAlmostEqual(production.total_material_cost, 30.0)
        self.assertAlmostEqual(production.total_labour_cost, 30.0)
        self.assertAlmostEqual(production.total_overhead_cost, 45.0)
        self.assertAlmostEqual(production.total_cost, 105.0)

    def test_action_cancel_button_returns_cancel_reason_wizard(self):
        production = self._create_production()

        action = production.action_cancel_button()

        self.assertEqual(action['res_model'], 'mrp.cancel.reason')
        self.assertEqual(action['target'], 'new')
        reason = self.env['mrp.cancel.reason'].browse(action['res_id'])
        self.assertEqual(reason.manufacturing_id, production)

    def test_button_mark_done_sets_missing_actual_cost_inputs(self):
        production = self._create_production()
        production.workorder_ids.write({'duration': 18.0})

        with patch(
            'odoo.addons.mrp.models.mrp_production.MrpProduction.button_mark_done',
            return_value=True,
        ):
            result = production.button_mark_done()

        self.assertTrue(result)
        self.assertAlmostEqual(production.material_cost_ids.actual_quantity, 3.0)
        self.assertAlmostEqual(production.labour_cost_ids.actual_minute, 18.0)
        self.assertAlmostEqual(production.overhead_cost_ids.actual_minute, 18.0)
        self.assertAlmostEqual(production.total_actual_material_cost, 30.0)
        self.assertAlmostEqual(production.total_actual_labour_cost, 36.0)
        self.assertAlmostEqual(production.total_actual_overhead_cost, 54.0)
        self.assertAlmostEqual(production.total_actual_cost, 120.0)
