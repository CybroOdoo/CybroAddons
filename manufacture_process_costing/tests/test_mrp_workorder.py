# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestMrpWorkorderCosting(TransactionCase):

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

    def _create_production(self):
        bom = self._prepare_bom_costs()
        production = self.env['mrp.production'].create({
            'product_id': self.finished_product.id,
            'product_qty': 1.0,
            'product_uom_id': self.uom_unit.id,
            'bom_id': bom.id,
        })
        production._onchange_bom_id()
        return production

    def test_button_finish_updates_actual_costs_from_workorder(self):
        self._set_costing_method('work-center')
        production = self._create_production()
        workorder = self.env['mrp.workorder'].create({
            'name': 'Assembly',
            'production_id': production.id,
            'workcenter_id': self.workcenter.id,
            'product_uom_id': self.uom_unit.id,
            'duration_expected': 15.0,
            'duration': 22.0,
        })

        with patch(
            'odoo.addons.mrp.models.mrp_workorder.MrpWorkorder.button_finish',
            return_value=True,
        ):
            result = workorder.button_finish()

        self.assertTrue(result)
        self.assertAlmostEqual(production.labour_cost_ids.actual_minute, 22.0)
        self.assertAlmostEqual(production.overhead_cost_ids.actual_minute, 22.0)
        self.assertAlmostEqual(production.material_cost_ids.actual_quantity, 3.0)
        self.assertAlmostEqual(production.total_actual_labour_cost, 44.0)
        self.assertAlmostEqual(production.total_actual_overhead_cost, 66.0)
