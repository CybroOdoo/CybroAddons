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
from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestManufactureProcessCosting(TransactionCase):
    """Test cases for the manufacture_process_costing module covering:
    - Work center cost per minute configuration
    - BOM estimated costing (Material, Labour, Overhead)
    - Syncing operations with process costs
    - MO planned vs actual process costing
    - Work order completion duration sync
    - MO cancellation reason wizard
    - BOM and Production cost report rendering
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_param = cls.env['ir.config_parameter'].sudo()

        # UoM
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        # Products
        cls.product_finished = cls.env['product.product'].create({
            'name': 'Test Finished Table',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
        })
        cls.component_wood = cls.env['product.product'].create({
            'name': 'Test Wood Top',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'lst_price': 50.0,
            'standard_price': 40.0,
        })
        cls.component_screw = cls.env['product.product'].create({
            'name': 'Test Metal Leg',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'lst_price': 15.0,
            'standard_price': 10.0,
        })

        # Work Center
        cls.workcenter = cls.env['mrp.workcenter'].create({
            'name': 'Test Assembly Work Center',
            'costs_hour': 60.0,
            'labour_cost': 1.5,     # 1.5 per minute
            'overhead_cost': 0.5,   # 0.5 per minute
        })

    def _set_costing_method(self, method):
        """Helper to set config parameter across Odoo versions."""
        if hasattr(self.config_param, 'set_str'):
            self.config_param.set_str('manufacture_process_costing.process_costing_method', method)
        else:
            self.config_param.set_param('manufacture_process_costing.process_costing_method', method)

    def test_01_workcenter_bom_estimated_costing(self):
        """Test BOM process costing calculation in 'work-center' mode."""
        self._set_costing_method('work-center')

        # Create BOM with components and operations
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_finished.product_tmpl_id.id,
            'product_id': self.product_finished.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                Command.create({
                    'product_id': self.component_wood.id,
                    'product_qty': 1.0,
                }),
                Command.create({
                    'product_id': self.component_screw.id,
                    'product_qty': 4.0,
                }),
            ],
            'operation_ids': [
                Command.create({
                    'name': 'Assembling Table',
                    'workcenter_id': self.workcenter.id,
                    'time_cycle_manual': 30.0,
                    'time_cycle': 30.0,
                }),
            ],
        })

        # Add material cost lines directly or via onchange simulation
        bom.material_cost_ids = [
            Command.create({
                'product_id': self.component_wood.id,
                'planned_qty': 1.0,
                'uom_id': self.uom_unit.id,
                'cost_unit': self.component_wood.lst_price,
            }),
            Command.create({
                'product_id': self.component_screw.id,
                'planned_qty': 4.0,
                'uom_id': self.uom_unit.id,
                'cost_unit': self.component_screw.lst_price,
            }),
        ]

        # Verify material costs: (1 * 50) + (4 * 15) = 50 + 60 = 110.0
        self.assertEqual(bom.total_material_cost, 110.0)

        # Verify labour cost: 30 minutes * 1.5 = 45.0
        self.assertEqual(len(bom.labour_cost_ids), 1)
        self.assertEqual(bom.labour_cost_ids.cost_minute, 1.5)
        self.assertEqual(bom.labour_cost_ids.planned_minute, 30.0)
        self.assertEqual(bom.total_labour_cost, 45.0)

        # Verify overhead cost: 30 minutes * 0.5 = 15.0
        self.assertEqual(len(bom.overhead_cost_ids), 1)
        self.assertEqual(bom.overhead_cost_ids.cost_minute, 0.5)
        self.assertEqual(bom.overhead_cost_ids.planned_minute, 30.0)
        self.assertEqual(bom.total_overhead_cost, 15.0)

    def test_02_manual_costing_mode(self):
        """Test BOM operation sync in 'manually' mode defaults cost_minute to 0.0."""
        self._set_costing_method('manually')

        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_finished.product_tmpl_id.id,
            'product_qty': 1.0,
            'operation_ids': [
                Command.create({
                    'name': 'Manual Polishing',
                    'workcenter_id': self.workcenter.id,
                    'time_cycle_manual': 20.0,
                    'time_cycle': 20.0,
                }),
            ],
        })

        # In manual mode, cost_minute defaults to 0.0
        self.assertEqual(bom.labour_cost_ids.cost_minute, 0.0)
        self.assertEqual(bom.overhead_cost_ids.cost_minute, 0.0)

        # User enters costs manually
        bom.labour_cost_ids.write({'cost_minute': 2.0})
        bom.overhead_cost_ids.write({'cost_minute': 1.0})

        self.assertEqual(bom.total_labour_cost, 40.0)    # 20 * 2.0
        self.assertEqual(bom.total_overhead_cost, 20.0)  # 20 * 1.0

    def test_03_manufacturing_order_costs_and_completion(self):
        """Test MO cost creation from BOM and actual cost calculation on work order finish."""
        self._set_costing_method('work-center')

        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_finished.product_tmpl_id.id,
            'product_id': self.product_finished.id,
            'product_qty': 1.0,
            'bom_line_ids': [
                Command.create({
                    'product_id': self.component_wood.id,
                    'product_qty': 1.0,
                }),
            ],
            'operation_ids': [
                Command.create({
                    'name': 'Cutting & Assembly',
                    'workcenter_id': self.workcenter.id,
                    'time_cycle_manual': 40.0,
                    'time_cycle': 40.0,
                }),
            ],
        })
        bom.material_cost_ids = [
            Command.create({
                'product_id': self.component_wood.id,
                'planned_qty': 1.0,
                'uom_id': self.uom_unit.id,
                'cost_unit': 50.0,
            }),
        ]

        # Create Manufacturing Order
        mo = self.env['mrp.production'].create({
            'product_id': self.product_finished.id,
            'bom_id': bom.id,
            'product_qty': 1.0,
        })

        # Ensure cost lines were synced from BOM
        self.assertTrue(mo.material_cost_ids)
        self.assertTrue(mo.labour_cost_ids)
        self.assertTrue(mo.overhead_cost_ids)
        self.assertEqual(mo.total_material_cost, 50.0)
        self.assertEqual(mo.total_labour_cost, 60.0)    # 40 * 1.5
        self.assertEqual(mo.total_overhead_cost, 20.0)  # 40 * 0.5
        self.assertEqual(mo.total_cost, 130.0)

        # Confirm MO to generate workorders
        mo.action_confirm()
        self.assertTrue(mo.workorder_ids)

        workorder = mo.workorder_ids[0]
        workorder.duration = 50.0  # Actually took 50 minutes instead of planned 40

        # Complete work order
        workorder.button_finish()

        # In work-center mode, actual minutes and actual material quantities sync
        labour_line = mo.labour_cost_ids.filtered(lambda l: l.operation == workorder.name)
        overhead_line = mo.overhead_cost_ids.filtered(lambda o: o.operation == workorder.name)
        material_line = mo.material_cost_ids[0]

        self.assertEqual(labour_line.actual_minute, 50.0)
        self.assertEqual(overhead_line.actual_minute, 50.0)
        self.assertEqual(material_line.actual_quantity, 1.0)

        # Actual totals
        self.assertEqual(mo.total_actual_material_cost, 50.0)   # 1.0 * 50.0
        self.assertEqual(mo.total_actual_labour_cost, 75.0)     # 50.0 * 1.5
        self.assertEqual(mo.total_actual_overhead_cost, 25.0)   # 50.0 * 0.5
        self.assertEqual(mo.total_actual_cost, 150.0)

    def test_04_mrp_cancel_reason_wizard(self):
        """Test the MO cancel reason wizard and history tracking."""
        mo = self.env['mrp.production'].create({
            'product_id': self.product_finished.id,
            'product_qty': 1.0,
        })
        mo.action_confirm()
        self.assertEqual(mo.state, 'confirmed')

        # Click cancel button opens the wizard action
        action = mo.action_cancel_button()
        self.assertEqual(action.get('res_model'), 'mrp.cancel.reason')

        reason_wizard = self.env['mrp.cancel.reason'].browse(action['res_id'])
        self.assertEqual(reason_wizard.manufacturing_id.id, mo.id)

        # Submit cancellation reason
        reason_wizard.reason_for_cancel = 'Customer canceled the order due to delay'
        reason_wizard.action_button_cancel()

        # MO is now canceled
        self.assertEqual(mo.state, 'cancel')

        # Reason record is preserved in database
        saved_reasons = self.env['mrp.cancel.reason'].search([
            ('manufacturing_id', '=', mo.id)
        ])
        self.assertTrue(saved_reasons)
        self.assertIn('Customer canceled', saved_reasons[0].reason_for_cancel)
        self.assertEqual(saved_reasons[0].cancelled_by_id.id, self.env.user.id)

    def test_05_reports_rendering(self):
        """Test that BOM and MO process cost reports render cleanly without error."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_finished.product_tmpl_id.id,
            'product_id': self.product_finished.id,
            'product_qty': 1.0,
            'bom_line_ids': [
                Command.create({
                    'product_id': self.component_wood.id,
                    'product_qty': 2.0,
                }),
            ],
            'operation_ids': [
                Command.create({
                    'name': 'Quality Inspection',
                    'workcenter_id': self.workcenter.id,
                    'time_cycle_manual': 15.0,
                    'time_cycle': 15.0,
                }),
            ],
        })

        mo = self.env['mrp.production'].create({
            'product_id': self.product_finished.id,
            'bom_id': bom.id,
            'product_qty': 1.0,
        })

        report_model = self.env['ir.actions.report']

        # Render BOM Cost Report
        bom_pdf, _ = report_model._render_qweb_pdf(
            'manufacture_process_costing.action_report_bom_cost', [bom.id]
        )
        self.assertTrue(bom_pdf)

        # Render MO Production Cost Report
        mo_pdf, _ = report_model._render_qweb_pdf(
            'manufacture_process_costing.action_production_cost_report', [mo.id]
        )
        self.assertTrue(mo_pdf)

