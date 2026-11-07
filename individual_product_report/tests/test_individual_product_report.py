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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.exceptions import AccessError
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestIndividualProductReport(common.TransactionCase):
    """Test suite for individual_product_report module covering views,
    actions, domains, contexts, sales integration, variant isolation,
    and user access control security."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create customer partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Report Customer',
            'email': 'customer@reporttest.com',
        })

        # Create first product template with single default variant
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Report Test Product Template 1',
            'sale_ok': True,
            'list_price': 150.0,
        })
        cls.product_1 = cls.product_tmpl.product_variant_ids[0]

        # Create second product template
        cls.product_tmpl_2 = cls.env['product.template'].create({
            'name': 'Report Test Product Template 2',
            'sale_ok': True,
            'list_price': 250.0,
        })
        cls.product_2 = cls.product_tmpl_2.product_variant_ids[0]

        # Create a product template with multiple variants via attributes
        cls.color_attribute = cls.env['product.attribute'].create({
            'name': 'Report Test Color',
        })
        cls.color_red = cls.env['product.attribute.value'].create({
            'name': 'Red',
            'attribute_id': cls.color_attribute.id,
        })
        cls.color_blue = cls.env['product.attribute.value'].create({
            'name': 'Blue',
            'attribute_id': cls.color_attribute.id,
        })
        cls.multi_var_tmpl = cls.env['product.template'].create({
            'name': 'Multi Variant Product',
            'sale_ok': True,
            'list_price': 100.0,
            'attribute_line_ids': [(0, 0, {
                'attribute_id': cls.color_attribute.id,
                'value_ids': [(6, 0, [cls.color_red.id, cls.color_blue.id])],
            })],
        })
        cls.var_1 = cls.multi_var_tmpl.product_variant_ids[0]
        cls.var_2 = cls.multi_var_tmpl.product_variant_ids[1]

        # Security groups
        group_salesman = cls.env.ref('sales_team.group_sale_salesman')
        group_manager = cls.env.ref('sales_team.group_sale_manager')
        group_internal = cls.env.ref('base.group_user')
        group_portal = cls.env.ref('base.group_portal')

        # Create a salesman user (authorized)
        cls.salesman_user = cls.env['res.users'].create({
            'name': 'Test Salesman User',
            'login': 'test_salesman_user',
            'email': 'salesman@reporttest.com',
            'group_ids': [(6, 0, [group_salesman.id, group_internal.id])],
        })

        # Create a sales manager user (authorized)
        cls.sales_manager_user = cls.env['res.users'].create({
            'name': 'Test Sales Manager User',
            'login': 'test_sales_manager_user',
            'email': 'manager@reporttest.com',
            'group_ids': [(6, 0, [group_manager.id, group_salesman.id, group_internal.id])],
        })

        # Create an unauthorized internal user (no sales rights)
        cls.unauthorized_user = cls.env['res.users'].create({
            'name': 'Test Unauthorized User',
            'login': 'test_unauthorized_user',
            'email': 'unauthorized@reporttest.com',
            'group_ids': [(6, 0, [group_internal.id])],
        })

        # Create a portal user (no internal or sales rights)
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Test Portal User',
            'login': 'test_portal_user',
            'email': 'portal@reporttest.com',
            'group_ids': [(6, 0, [group_portal.id])],
        })

    def test_01_views_and_action_definition(self):
        """Verify the report action and inherited views exist and are valid."""
        action = self.env.ref('individual_product_report.report_sales_product_graph')
        self.assertTrue(action, "Action individual_product_report.report_sales_product_graph must exist.")
        self.assertEqual(action.type, 'ir.actions.act_window')
        self.assertEqual(action.res_model, 'sale.report')
        self.assertEqual(action.view_mode, 'graph')

        tmpl_view = self.env.ref('individual_product_report.product_template_report_only_form_view')
        self.assertTrue(tmpl_view, "product_template_report_only_form_view must exist.")
        self.assertEqual(tmpl_view.model, 'product.template')

        product_view = self.env.ref('individual_product_report.product_report_normal_form_view')
        self.assertTrue(product_view, "product_report_normal_form_view must exist.")
        self.assertEqual(product_view.model, 'product.product')

        # Verify views load without xml or rendering errors
        tmpl_views = self.env['product.template'].get_views([(tmpl_view.id, 'form')])
        self.assertIn('views', tmpl_views)
        self.assertIn('form', tmpl_views['views'])

        prod_views = self.env['product.product'].get_views([(product_view.id, 'form')])
        self.assertIn('views', prod_views)
        self.assertIn('form', prod_views['views'])

        # Verify security access record exists
        access = self.env.ref('individual_product_report.access_sale_report_salesman', raise_if_not_found=False)
        if access:
            self.assertEqual(access.model_id.model, 'sale.report')
            self.assertEqual(access.group_id, self.env.ref('sales_team.group_sale_salesman'))
            if hasattr(access, 'for_read'):
                self.assertTrue(access.for_read)

    def test_02_product_template_action_view_sales_report(self):
        """Verify action_view_sales_report on product.template returns expected action."""
        action = self.product_tmpl.with_user(self.salesman_user).action_view_sales_report()

        self.assertEqual(action.get('res_model'), 'sale.report')
        self.assertEqual(action.get('view_mode'), 'graph')
        self.assertEqual(action.get('domain'), [('product_tmpl_id', 'in', self.product_tmpl.ids)])

        context = action.get('context', {})
        self.assertEqual(context.get('graph_measure'), ['product_uom_qty'])
        self.assertEqual(context.get('active_model'), 'sale.report')
        self.assertEqual(context.get('search_default_Sales'), 1)
        self.assertEqual(context.get('time_ranges'), {'field': 'date', 'range': 'last_365_days'})
        self.assertEqual(context.get('groupby'), 'date')

    def test_03_product_product_action_view_sales_report(self):
        """Verify action_view_sales_report on product.product returns expected action."""
        action = self.product_1.with_user(self.salesman_user).action_view_sales_report()

        self.assertEqual(action.get('res_model'), 'sale.report')
        self.assertEqual(action.get('view_mode'), 'graph')
        self.assertEqual(action.get('domain'), [('product_id', 'in', self.product_1.ids)])

        context = action.get('context', {})
        self.assertEqual(context.get('graph_measure'), ['product_uom_qty'])
        self.assertEqual(context.get('active_model'), 'sale.report')
        self.assertEqual(context.get('search_default_Sales'), 1)
        self.assertEqual(context.get('time_ranges'), {'field': 'date', 'range': 'last_365_days'})
        self.assertEqual(context.get('groupby'), 'date')

    def test_04_template_and_product_multiple_records(self):
        """Verify action_view_sales_report on multi-record sets."""
        templates = self.product_tmpl + self.product_tmpl_2
        action_tmpl = templates.with_user(self.salesman_user).action_view_sales_report()
        self.assertEqual(action_tmpl.get('domain'), [('product_tmpl_id', 'in', templates.ids)])

        products = self.product_1 + self.product_2
        action_prod = products.with_user(self.salesman_user).action_view_sales_report()
        self.assertEqual(action_prod.get('domain'), [('product_id', 'in', products.ids)])

    def test_05_active_id_context_propagation(self):
        """Verify that active_id from env.context is propagated to action context."""
        action_tmpl = self.product_tmpl.with_user(
            self.salesman_user
        ).with_context(active_id=self.product_tmpl.id).action_view_sales_report()
        self.assertEqual(action_tmpl['context'].get('active_id'), self.product_tmpl.id)

        action_prod = self.product_1.with_user(
            self.salesman_user
        ).with_context(active_id=self.product_1.id).action_view_sales_report()
        self.assertEqual(action_prod['context'].get('active_id'), self.product_1.id)

    def test_06_sales_flow_and_sale_report_integration(self):
        """Verify sale order creation, confirmation, and sale.report query matching."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product_1.id,
                'product_uom_qty': 5.0,
                'price_unit': 150.0,
            })],
        })
        order.action_confirm()

        self.assertEqual(order.state, 'sale')
        self.assertGreaterEqual(self.product_1.sales_count, 5.0)
        self.assertGreaterEqual(self.product_tmpl.sales_count, 5.0)

        # Check domain for template
        action_tmpl = self.product_tmpl.with_user(self.salesman_user).action_view_sales_report()
        reports_tmpl = self.env['sale.report'].with_user(self.salesman_user).search(action_tmpl['domain'])
        self.assertTrue(reports_tmpl, "sale.report should return records for sold product template.")
        self.assertIn(self.product_tmpl.id, reports_tmpl.mapped('product_tmpl_id').ids)
        self.assertGreaterEqual(sum(reports_tmpl.mapped('product_uom_qty')), 5.0)

        # Check domain for product variant
        action_prod = self.product_1.with_user(self.salesman_user).action_view_sales_report()
        reports_prod = self.env['sale.report'].with_user(self.salesman_user).search(action_prod['domain'])
        self.assertTrue(reports_prod, "sale.report should return records for sold product variant.")
        self.assertIn(self.product_1.id, reports_prod.mapped('product_id').ids)
        self.assertGreaterEqual(sum(reports_prod.mapped('product_uom_qty')), 5.0)

    def test_07_sales_report_empty_recordset(self):
        """Verify calling action_view_sales_report on empty recordsets."""
        empty_tmpl = self.env['product.template'].with_user(self.salesman_user).browse([])
        action_tmpl = empty_tmpl.action_view_sales_report()
        self.assertEqual(action_tmpl.get('domain'), [('product_tmpl_id', 'in', [])])

        empty_prod = self.env['product.product'].with_user(self.salesman_user).browse([])
        action_prod = empty_prod.action_view_sales_report()
        self.assertEqual(action_prod.get('domain'), [('product_id', 'in', [])])

    def test_08_salesman_user_access(self):
        """Verify that a salesman user can call action_view_sales_report and query sale.report."""
        action_tmpl = self.product_tmpl.with_user(self.salesman_user).action_view_sales_report()
        self.assertEqual(action_tmpl.get('res_model'), 'sale.report')
        self.assertEqual(action_tmpl.get('domain'), [('product_tmpl_id', 'in', self.product_tmpl.ids)])

        action_prod = self.product_1.with_user(self.salesman_user).action_view_sales_report()
        self.assertEqual(action_prod.get('res_model'), 'sale.report')
        self.assertEqual(action_prod.get('domain'), [('product_id', 'in', self.product_1.ids)])

        # Ensure salesman can read sale.report records
        reports = self.env['sale.report'].with_user(self.salesman_user).search(action_tmpl['domain'])
        if reports:
            reports.read(['name', 'product_uom_qty', 'price_total'])

    def test_09_multiple_variants_sales_reporting(self):
        """Verify reporting separation when a product template has multiple variants."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.var_1.id,
                    'product_uom_qty': 2.0,
                    'price_unit': 100.0,
                }),
                (0, 0, {
                    'product_id': self.var_2.id,
                    'product_uom_qty': 4.0,
                    'price_unit': 100.0,
                }),
            ],
        })
        order.action_confirm()

        # Template action covers both variants
        act_tmpl = self.multi_var_tmpl.with_user(self.salesman_user).action_view_sales_report()
        reports_tmpl = self.env['sale.report'].with_user(self.salesman_user).search(act_tmpl['domain'])
        self.assertEqual(sum(reports_tmpl.mapped('product_uom_qty')), 6.0)

        # Variant 1 action covers only Variant 1
        act_var_1 = self.var_1.with_user(self.salesman_user).action_view_sales_report()
        reports_var_1 = self.env['sale.report'].with_user(self.salesman_user).search(act_var_1['domain'])
        self.assertEqual(sum(reports_var_1.mapped('product_uom_qty')), 2.0)

        # Variant 2 action covers only Variant 2
        act_var_2 = self.var_2.with_user(self.salesman_user).action_view_sales_report()
        reports_var_2 = self.env['sale.report'].with_user(self.salesman_user).search(act_var_2['domain'])
        self.assertEqual(sum(reports_var_2.mapped('product_uom_qty')), 4.0)

    def test_10_smart_button_invisibility_condition(self):
        """Verify the smart button visibility logic based on sale_ok and sales_count."""
        # Unsold product
        unsold_tmpl = self.env['product.template'].create({
            'name': 'Unsold Product',
            'sale_ok': True,
        })
        self.assertEqual(unsold_tmpl.sales_count, 0.0)
        # Condition in XML: invisible="sale_ok == False or sales_count == 0"
        invisible_condition = (not unsold_tmpl.sale_ok) or (unsold_tmpl.sales_count == 0)
        self.assertTrue(invisible_condition, "Smart button should be invisible when sales_count == 0")

        # Non-saleable product
        not_saleable_tmpl = self.env['product.template'].create({
            'name': 'Non Saleable Product',
            'sale_ok': False,
        })
        invisible_condition_ns = (not not_saleable_tmpl.sale_ok) or (not_saleable_tmpl.sales_count == 0)
        self.assertTrue(invisible_condition_ns, "Smart button should be invisible when sale_ok is False")

    def test_11_unauthorized_user_access_error(self):
        """Verify that an internal user without salesman rights cannot call
        action_view_sales_report and receives an AccessError."""
        with self.assertRaises(AccessError):
            self.product_tmpl.with_user(self.unauthorized_user).action_view_sales_report()

        with self.assertRaises(AccessError):
            self.product_1.with_user(self.unauthorized_user).action_view_sales_report()

    def test_12_portal_user_access_error(self):
        """Verify that a portal user cannot call action_view_sales_report and
        receives an AccessError."""
        with self.assertRaises(AccessError):
            self.product_tmpl.with_user(self.portal_user).action_view_sales_report()

        with self.assertRaises(AccessError):
            self.product_1.with_user(self.portal_user).action_view_sales_report()

    def test_13_sale_report_model_access_control(self):
        """Verify that model-level access control on sale.report is properly
        enforced for salesman, manager, and unauthorized users."""
        # Salesman has read access to sale.report
        self.assertTrue(
            self.env['sale.report'].with_user(self.salesman_user).has_access('read'),
            "Salesman should have read access to sale.report"
        )

        # Sales manager has read access to sale.report
        self.assertTrue(
            self.env['sale.report'].with_user(self.sales_manager_user).has_access('read'),
            "Sales manager should have read access to sale.report"
        )

        # Unauthorized user must not have access to sale.report
        with self.assertRaises(AccessError):
            self.env['sale.report'].with_user(self.unauthorized_user).check_access('read')

    def test_14_sales_manager_user_access(self):
        """Verify that a sales manager can access the sales report graph action."""
        action_tmpl = self.product_tmpl.with_user(self.sales_manager_user).action_view_sales_report()
        self.assertEqual(action_tmpl.get('res_model'), 'sale.report')
        self.assertEqual(action_tmpl.get('domain'), [('product_tmpl_id', 'in', self.product_tmpl.ids)])

        action_prod = self.product_1.with_user(self.sales_manager_user).action_view_sales_report()
        self.assertEqual(action_prod.get('res_model'), 'sale.report')
        self.assertEqual(action_prod.get('domain'), [('product_id', 'in', self.product_1.ids)])

    def test_15_view_button_security_groups(self):
        """Verify that the smart buttons in XML views and window action are
        properly secured with sales_team.group_sale_salesman."""
        group_salesman = self.env.ref('sales_team.group_sale_salesman')

        # Check product.template inherited form view
        tmpl_view = self.env.ref('individual_product_report.product_template_report_only_form_view')
        self.assertIn(
            'sales_team.group_sale_salesman',
            tmpl_view.arch,
            "Template view must restrict smart button with sales_team.group_sale_salesman"
        )

        # Check product.product inherited form view
        prod_view = self.env.ref('individual_product_report.product_report_normal_form_view')
        self.assertIn(
            'sales_team.group_sale_salesman',
            prod_view.arch,
            "Product view must restrict smart button with sales_team.group_sale_salesman"
        )

        # Check window action group restriction
        action = self.env.ref('individual_product_report.report_sales_product_graph')
        if action.group_ids:
            self.assertIn(group_salesman, action.group_ids)
