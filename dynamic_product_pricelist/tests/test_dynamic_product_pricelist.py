# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Henna Mehjabin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestDynamicProductPricelist(TransactionCase):
    """Test suite for the dynamic product pricelist columns,

    covering the security group, the generated fields and views, the price
    calculation for global, category, product and variant rules, the rule
    precedence, the refresh on rule changes, and the clean up when the
    pricelist is hidden or deleted.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pricelist_model = cls.env['product.pricelist']
        cls.view_model = cls.env['ir.ui.view']
        cls.field_model = cls.env['ir.model.fields']
        cls.tmpl_model_id = cls.env.ref('product.model_product_template').id
        cls.var_model_id = cls.env.ref('product.model_product_product').id

        cls.parent_categ = cls.env['product.category'].create({
            'name': 'Test Parent Category',
        })
        cls.child_categ = cls.env['product.category'].create({
            'name': 'Test Child Category',
            'parent_id': cls.parent_categ.id,
        })
        cls.other_categ = cls.env['product.category'].create({
            'name': 'Test Other Category',
        })
        cls.tmpl_child = cls._create_template(
            'Test Child Product', cls.child_categ, 100.0)
        cls.tmpl_child_2 = cls._create_template(
            'Test Second Child Product', cls.child_categ, 150.0)
        cls.tmpl_other = cls._create_template(
            'Test Other Product', cls.other_categ, 200.0)

    @classmethod
    def _create_template(cls, name, categ, list_price):
        """Create a product template in the given category."""
        return cls.env['product.template'].create({
            'name': name,
            'categ_id': categ.id,
            'list_price': list_price,
        })

    @classmethod
    def _get_item_vals(cls, applied_on, fixed_price=0.0, **kwargs):
        """Return the values of a fixed price pricelist rule."""
        vals = {
            'applied_on': applied_on,
            'compute_price': 'fixed',
            'fixed_price': fixed_price,
        }
        vals.update(kwargs)
        return vals

    def _create_pricelist(self, name='Dynamic Test List', items=None,
                          show=True):
        """Create a pricelist with the given rules and display flag."""
        vals = {
            'name': name,
            'is_show_product_pricelist': show,
        }
        if items:
            vals['item_ids'] = [Command.create(item) for item in items]
        return self.pricelist_model.create(vals)

    def _get_dynamic_field(self, pricelist, prefix='temp_'):
        """Return the dynamic field generated for the pricelist."""
        model_id = (self.tmpl_model_id if prefix == 'temp_'
                    else self.var_model_id)
        return pricelist._get_pricelist_field(prefix, model_id)

    def _get_price(self, pricelist, record, prefix='temp_'):
        """Return the value stored in the pricelist column of a record."""
        field = self._get_dynamic_field(pricelist, prefix)
        self.assertTrue(field, 'The dynamic pricelist field is missing.')
        self.env.invalidate_all()
        return record[field.name]

    def _get_views(self, pricelist, model='product.template', active=True):
        """Return the generated list views of the pricelist."""
        pricelist_name = pricelist.name.replace(' ', '_')
        return self.view_model.with_context(active_test=False).search([
            ('name', '=', f'product.dynamic.fields.{pricelist_name}'),
            ('model', '=', model),
            ('active', '=', active),
        ])

    def test_01_security_group(self):
        """Verify the dynamic pricelist group and its privilege are created."""
        group = self.env.ref(
            'dynamic_product_pricelist.group_show_sale_pricelist')
        self.assertEqual(group.name, 'Show dynamic pricelist')
        self.assertEqual(group.privilege_id.name, 'Dynamic Pricelist')
        self.assertIn(self.env.ref('base.group_user'), group.implied_ids)

    def test_02_flag_field_attributes(self):
        """Verify the display flag is a boolean which is off by default."""
        field = self.pricelist_model._fields['is_show_product_pricelist']
        self.assertEqual(field.type, 'boolean')
        pricelist = self.pricelist_model.create({'name': 'Plain List'})
        self.assertFalse(pricelist.is_show_product_pricelist)

    def test_03_pricelist_form_view_shows_flag(self):
        """Verify the pricelist form view is extended with the display flag."""
        view = self.env.ref('dynamic_product_pricelist.product_pricelist_view')
        self.assertEqual(
            view.inherit_id, self.env.ref('product.product_pricelist_view'))
        self.assertIn('is_show_product_pricelist', view.arch_db)

    def test_04_flag_disabled_creates_nothing(self):
        """Verify no field or view is generated while the flag is off."""
        pricelist = self._create_pricelist(
            name='Hidden Test List', show=False, items=[
                self._get_item_vals('3_global', 10.0)])
        self.assertFalse(self._get_dynamic_field(pricelist))
        self.assertFalse(self._get_views(pricelist))

    def test_05_flag_enabled_creates_field_and_view(self):
        """Verify the flag creates a float field and a view on the template."""
        pricelist = self._create_pricelist(name='Shown Test List')
        field = self._get_dynamic_field(pricelist)
        self.assertTrue(field)
        self.assertEqual(field.ttype, 'float')
        self.assertEqual(field.field_description, 'Shown_Test_List')
        self.assertEqual(field.name, f'x_temp_{pricelist.id}Shown_Test_List')

        view = self._get_views(pricelist)
        self.assertEqual(len(view), 1)
        self.assertEqual(view.type, 'list')
        self.assertEqual(
            view.inherit_id,
            self.env.ref('product.product_template_tree_view'))
        self.assertIn(field.name, view.arch_base)
        self.assertIn('group_show_sale_pricelist', view.arch_base)

    def test_06_variant_field_only_with_variant_rule(self):
        """Verify the variant field is created only for variant rules."""
        pricelist = self._create_pricelist(name='Variant Test List')
        self.assertFalse(self._get_dynamic_field(pricelist, 'variant_'))
        self.assertFalse(self._get_views(pricelist, 'product.product'))

        variant = self.tmpl_child.product_variant_id
        self.env['product.pricelist.item'].create(dict(
            self._get_item_vals('0_product_variant', 45.0),
            pricelist_id=pricelist.id, product_id=variant.id))

        field_var = self._get_dynamic_field(pricelist, 'variant_')
        self.assertTrue(field_var)
        self.assertEqual(field_var.ttype, 'float')
        self.assertEqual(len(self._get_views(pricelist, 'product.product')), 1)
        self.assertEqual(
            self._get_price(pricelist, variant, 'variant_'), 45.0)
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 45.0)

    def test_07_global_rule_fixed_price(self):
        """Verify a global rule writes its price on every product."""
        pricelist = self._create_pricelist(items=[
            self._get_item_vals('3_global', 50.0)])
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 50.0)
        self.assertEqual(self._get_price(pricelist, self.tmpl_other), 50.0)

    def test_08_category_rule_includes_child_categories(self):
        """Verify a category rule applies to products of its child categories
        only and leaves the other categories untouched.
        """
        pricelist = self._create_pricelist(items=[
            self._get_item_vals(
                '2_product_category', 30.0, categ_id=self.parent_categ.id)])
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 30.0)
        self.assertEqual(self._get_price(pricelist, self.tmpl_other), 0.0)

    def test_09_product_rule_fixed_price(self):
        """Verify a product rule applies to that product only."""
        pricelist = self._create_pricelist(items=[
            self._get_item_vals(
                '1_product', 25.0, product_tmpl_id=self.tmpl_child.id)])
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 25.0)
        self.assertEqual(self._get_price(pricelist, self.tmpl_child_2), 0.0)
        self.assertEqual(self._get_price(pricelist, self.tmpl_other), 0.0)

    def test_10_discount_rule_computes_price(self):
        """Verify a discount rule computes the price from the sales price."""
        pricelist = self._create_pricelist(items=[{
            'applied_on': '3_global',
            'compute_price': 'discount',
            'base': 'list_price',
            'price_discount': 10.0,
        }])
        self.assertAlmostEqual(
            self._get_price(pricelist, self.tmpl_child), 90.0)
        self.assertAlmostEqual(
            self._get_price(pricelist, self.tmpl_other), 180.0)

    def test_11_rule_precedence(self):
        """Verify product rules win over category rules, and category rules
        win over global rules.
        """
        pricelist = self._create_pricelist(items=[
            self._get_item_vals('3_global', 10.0),
            self._get_item_vals(
                '2_product_category', 20.0, categ_id=self.parent_categ.id),
            self._get_item_vals(
                '1_product', 30.0, product_tmpl_id=self.tmpl_child.id),
        ])
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 30.0)
        self.assertEqual(self._get_price(pricelist, self.tmpl_child_2), 20.0)
        self.assertEqual(self._get_price(pricelist, self.tmpl_other), 10.0)

    def test_12_adding_rule_refreshes_prices(self):
        """Verify a rule added to an existing pricelist updates the column."""
        pricelist = self._create_pricelist()
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 0.0)

        self.env['product.pricelist.item'].create(dict(
            self._get_item_vals('3_global', 60.0), pricelist_id=pricelist.id))
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 60.0)

    def test_13_editing_rule_refreshes_prices(self):
        """Verify editing a rule updates the column."""
        pricelist = self._create_pricelist(items=[
            self._get_item_vals('3_global', 60.0)])
        pricelist.item_ids.fixed_price = 75.0
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 75.0)

    def test_14_changing_rule_target_resets_old_products(self):
        """Verify products no longer matching a rule are reset to zero."""
        pricelist = self._create_pricelist(items=[
            self._get_item_vals(
                '2_product_category', 40.0, categ_id=self.child_categ.id)])
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 40.0)
        self.assertEqual(self._get_price(pricelist, self.tmpl_other), 0.0)

        pricelist.item_ids.categ_id = self.other_categ
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 0.0)
        self.assertEqual(self._get_price(pricelist, self.tmpl_other), 40.0)

    def test_15_deleting_rule_resets_prices(self):
        """Verify deleting the last rule resets the column to zero."""
        pricelist = self._create_pricelist(items=[
            self._get_item_vals('3_global', 55.0)])
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 55.0)

        pricelist.item_ids.unlink()
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 0.0)
        self.assertEqual(self._get_price(pricelist, self.tmpl_other), 0.0)

    def test_16_archived_product_price_is_reset(self):
        """Verify archived products are reset when the rule is removed."""
        pricelist = self._create_pricelist(items=[
            self._get_item_vals('3_global', 35.0)])
        self.tmpl_child.active = False
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 35.0)

        pricelist.item_ids.unlink()
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 0.0)

    def test_17_rules_ignored_when_flag_disabled(self):
        """Verify rules of a pricelist without the flag generate nothing."""
        pricelist = self._create_pricelist(
            name='Ignored Test List', show=False)
        self.env['product.pricelist.item'].create(dict(
            self._get_item_vals('3_global', 20.0), pricelist_id=pricelist.id))
        self.assertFalse(self._get_dynamic_field(pricelist))
        self.assertFalse(self._get_views(pricelist))

    def test_18_disabling_flag_hides_view_and_resets_prices(self):
        """Verify disabling the flag deactivates the view and clears prices."""
        pricelist = self._create_pricelist(items=[
            self._get_item_vals('3_global', 65.0)])
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 65.0)
        self.assertEqual(len(self._get_views(pricelist)), 1)

        pricelist.is_show_product_pricelist = False
        self.assertFalse(self._get_views(pricelist, active=True))
        self.assertEqual(len(self._get_views(pricelist, active=False)), 1)
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 0.0)

    def test_19_enabling_flag_again_restores_prices(self):
        """Verify enabling the flag again shows the view and the prices."""
        pricelist = self._create_pricelist(items=[
            self._get_item_vals('3_global', 65.0)])
        pricelist.is_show_product_pricelist = False
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 0.0)

        pricelist.is_show_product_pricelist = True
        self.assertTrue(self._get_views(pricelist, active=True))
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 65.0)

    def test_20_unlink_removes_fields_and_views(self):
        """Verify deleting the pricelist removes its fields and views."""
        pricelist = self._create_pricelist(
            name='Deleted Test List', items=[
                self._get_item_vals('3_global', 15.0),
                self._get_item_vals(
                    '0_product_variant', 25.0,
                    product_id=self.tmpl_child.product_variant_id.id),
            ])
        field_names = [
            self._get_dynamic_field(pricelist).name,
            self._get_dynamic_field(pricelist, 'variant_').name,
        ]
        self.assertTrue(self._get_views(pricelist))
        self.assertTrue(self._get_views(pricelist, 'product.product'))

        pricelist_name = pricelist.name.replace(' ', '_')
        pricelist.unlink()
        self.assertFalse(self.view_model.with_context(
            active_test=False).search([
                ('name', '=', f'product.dynamic.fields.{pricelist_name}')]))
        self.assertFalse(self.field_model.search([
            ('name', 'in', field_names)]))

    def test_21_special_characters_in_name(self):
        """Verify a pricelist name with characters not allowed in a column
        name still generates a valid field and shows its prices.
        """
        pricelist = self._create_pricelist(
            name='B2B - Retail (EUR) 10%', items=[
                self._get_item_vals('3_global', 12.0)])
        field = self._get_dynamic_field(pricelist)
        self.assertTrue(field)
        self.assertRegex(field.name, r'^x_temp_\d+[A-Za-z0-9_]+$')
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 12.0)

    def test_22_long_name_is_truncated(self):
        """Verify a long pricelist name gives a field name of max 63 chars."""
        pricelist = self._create_pricelist(name='Long Name ' * 10)
        field = self._get_dynamic_field(pricelist)
        self.assertTrue(field)
        self.assertLessEqual(len(field.name), 63)

    def test_23_toggle_flag_does_not_duplicate_views(self):
        """Verify disabling and enabling the flag several times keeps a
        single template view and a single variant view.
        """
        pricelist = self._create_pricelist(items=[
            self._get_item_vals('3_global', 15.0),
            self._get_item_vals(
                '0_product_variant', 25.0,
                product_id=self.tmpl_child.product_variant_id.id),
        ])
        for _i in range(3):
            pricelist.is_show_product_pricelist = False
            pricelist.is_show_product_pricelist = True
        for model in ('product.template', 'product.product'):
            self.assertEqual(len(self._get_views(pricelist, model)), 1)
            self.assertFalse(self._get_views(pricelist, model, active=False))

    def test_24_rename_reuses_field_and_view(self):
        """Verify renaming a pricelist keeps its field and renames its view
        instead of creating new ones, and that it can still be deleted.
        """
        pricelist = self._create_pricelist(
            name='Before Rename', items=[self._get_item_vals('3_global', 5.0)])
        field = self._get_dynamic_field(pricelist)

        pricelist.name = 'After Rename'
        self.assertEqual(self._get_dynamic_field(pricelist), field)
        self.assertEqual(len(self._get_views(pricelist)), 1)
        self.assertFalse(self.view_model.with_context(
            active_test=False).search([
                ('name', '=', 'product.dynamic.fields.Before_Rename')]))
        self.assertEqual(self._get_price(pricelist, self.tmpl_child), 5.0)

        field_name = field.name
        pricelist.unlink()
        self.assertFalse(self.field_model.search([('name', '=', field_name)]))

    def test_25_same_name_pricelists_have_own_views(self):
        """Verify two pricelists with the same name each get their own view,
        and hiding one keeps the other visible.
        """
        first = self._create_pricelist(name='Twin List')
        second = self._create_pricelist(name='Twin List')
        self.assertEqual(len(self._get_views(first)), 2)

        first.is_show_product_pricelist = False
        second_field = self._get_dynamic_field(second)
        active_views = self._get_views(second)
        self.assertEqual(len(active_views), 1)
        self.assertIn(second_field.name, active_views.arch_db)

    def test_26_unlink_keeps_other_pricelist_fields(self):
        """Verify deleting a pricelist does not remove fields whose name only
        starts with the same id (e.g. pricelist 1 vs pricelist 10).
        """
        pricelist = self._create_pricelist(name='Owner List')
        other_field = self.field_model.create({
            'name': f'x_temp_{pricelist.id}0Other_List',
            'field_description': 'Other_List',
            'model_id': self.tmpl_model_id,
            'ttype': 'float',
        })
        pricelist.unlink()
        self.assertTrue(other_field.exists())

    def test_27_unlink_removes_archived_views(self):
        """Verify deleting a hidden pricelist removes its archived views."""
        pricelist = self._create_pricelist(name='Archived Delete List')
        field_name = self._get_dynamic_field(pricelist).name
        pricelist.is_show_product_pricelist = False
        self.assertEqual(len(self._get_views(pricelist, active=False)), 1)

        pricelist.unlink()
        self.assertFalse(self.view_model.with_context(
            active_test=False).search([
                ('name', '=', 'product.dynamic.fields.Archived_Delete_List')]))
        self.assertFalse(self.field_model.search([('name', '=', field_name)]))
