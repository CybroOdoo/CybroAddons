from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import SaleCommon


@tagged('post_install', '-at_install')
class TestSaleOrderWarranty(SaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warranty_product = cls.env['product.product'].create({
            'name': 'Warranty Product',
            'type': 'consu',
            'list_price': 120.0,
            'is_warranty_available': True,
            'warranty_duration': 12,
            'taxes_id': [Command.clear()],
        })
        cls.non_warranty_product = cls.env['product.product'].create({
            'name': 'Non Warranty Product',
            'type': 'consu',
            'list_price': 80.0,
            'is_warranty_available': False,
            'taxes_id': [Command.clear()],
        })

    def test_action_confirm_sets_warranty_flag_when_any_line_has_warranty(self):
        order = self._create_so(order_line=[
            Command.create({'product_id': self.non_warranty_product.id}),
            Command.create({'product_id': self.warranty_product.id}),
        ])

        order.action_confirm()

        self.assertTrue(order.is_warranty_check)

    def test_action_confirm_clears_warranty_flag_without_warranty_lines(self):
        order = self._create_so(order_line=[
            Command.create({'product_id': self.non_warranty_product.id}),
        ])

        order.action_confirm()

        self.assertFalse(order.is_warranty_check)

    def test_action_open_smart_tab_updates_expiry_and_returns_action(self):
        order = self._create_so(order_line=[
            Command.create({'product_id': self.warranty_product.id}),
        ])
        order.date_order = fields.Datetime.to_datetime('2026-03-10 09:00:00')

        action = order.action_open_smart_tab()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'product.template')
        self.assertEqual(
            action['domain'],
            [
                ('id', 'in', order.order_line.mapped('product_id.product_tmpl_id.id')),
                ('is_warranty_available', '=', True),
            ],
        )
        self.assertEqual(
            self.warranty_product.product_tmpl_id.warranty_expiry,
            order.date_order.date() + relativedelta(months=12),
        )
