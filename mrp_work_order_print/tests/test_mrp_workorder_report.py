# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMrpWorkOrderReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.workcenter = cls.env['mrp.workcenter'].create({
            'name': 'Assembly Station 1',
            'time_efficiency': 100,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Table',
            'type': 'consu',
        })
        cls.component = cls.env['product.product'].create({
            'name': 'Table Leg',
            'type': 'consu',
        })
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': cls.component.id,
                    'product_qty': 4.0,
                }),
            ],
            'operation_ids': [
                (0, 0, {
                    'name': 'Assembly Operation',
                    'workcenter_id': cls.workcenter.id,
                    'time_cycle': 60,
                }),
            ],
        })

    def test_report_action_definition(self):
        """Verify the report action is properly defined for mrp.workorder."""
        report = self.env.ref('mrp_work_order_print.action_report_work_order')
        self.assertEqual(report.name, 'Work Order Details')
        self.assertEqual(report.model, 'mrp.workorder')
        self.assertEqual(report.report_name, 'mrp_work_order_print.report_workorder')

    def test_render_workorder_report(self):
        """Verify rendering of the work order QWeb report."""
        production = self.env['mrp.production'].create({
            'product_id': self.product.id,
            'bom_id': self.bom.id,
            'product_qty': 1.0,
        })
        production.action_confirm()

        workorder = production.workorder_ids[:1]
        self.assertTrue(workorder, "Work order should be generated on MO confirmation")

        # Create time tracking record
        loss_reason = self.env['mrp.workcenter.productivity.loss'].search([], limit=1)
        if not loss_reason:
            loss_reason = self.env['mrp.workcenter.productivity.loss'].create({
                'name': 'Normal Operation',
                'loss_type': 'productive',
            })
        self.env['mrp.workcenter.productivity'].create({
            'workorder_id': workorder.id,
            'workcenter_id': self.workcenter.id,
            'loss_id': loss_reason.id,
            'duration': 30.0,
            'user_id': self.env.user.id,
        })

        # Test rendering report QWeb template
        rendered_html = self.env['ir.qweb']._render(
            'mrp_work_order_print.report_workorder',
            {'docs': workorder}
        )
        self.assertIn('Work Order Details', str(rendered_html))
        self.assertIn(self.workcenter.name, str(rendered_html))
        self.assertIn(self.product.name, str(rendered_html))
