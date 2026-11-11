# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import date

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase, new_test_user
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestProductVendorUpdate(TransactionCase):
    """Tests for the bulk vendor update wizard (product_multi_vendor_update)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env['res.partner'].create({'name': 'Test Vendor A'})
        cls.vendor_b = cls.env['res.partner'].create({'name': 'Test Vendor B'})
        cls.product_1 = cls.env['product.template'].create(
            {'name': 'Bulk Product 1', 'type': 'consu'})
        cls.product_2 = cls.env['product.template'].create(
            {'name': 'Bulk Product 2', 'type': 'consu'})
        cls.product_3 = cls.env['product.template'].create(
            {'name': 'Bulk Product 3', 'type': 'consu'})
        cls.products = cls.product_1 | cls.product_2 | cls.product_3

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _create_wizard(self, **vals):
        values = {'partner_id': self.vendor.id}
        values.update(vals)
        return self.env['product.vendor.update'].create(values)

    def _run_wizard(self, products, **vals):
        wizard = self._create_wizard(**vals).with_context(
            active_ids=products.ids, active_model='product.template')
        wizard.action_update_vendor()
        return wizard

    # ------------------------------------------------------------------
    # action / entry point
    # ------------------------------------------------------------------
    def test_product_method_returns_wizard_action(self):
        action = self.product_1.product_multi_vendor_update()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'product.vendor.update')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['view_mode'], 'form')

    def test_server_action_bound_to_product_template(self):
        action = self.env.ref(
            'product_multi_vendor_update.product_multi_vendor_update')
        self.assertEqual(action.model_id.model, 'product.template')
        self.assertEqual(action.binding_model_id.model, 'product.template')
        self.assertIn('list', action.binding_view_types)
        self.assertIn('form', action.binding_view_types)

    def test_server_action_run_returns_wizard(self):
        action = self.env.ref(
            'product_multi_vendor_update.product_multi_vendor_update')
        result = action.with_context(
            active_model='product.template',
            active_id=self.product_1.id,
            active_ids=self.products.ids).run()
        self.assertEqual(result['res_model'], 'product.vendor.update')

    # ------------------------------------------------------------------
    # wizard defaults / constraints
    # ------------------------------------------------------------------
    def test_wizard_default_currency_is_company_currency(self):
        wizard = self.env['product.vendor.update'].new({})
        self.assertEqual(wizard.currency_id, self.env.company.currency_id)

    @mute_logger('odoo.sql_db')
    def test_wizard_requires_vendor(self):
        with self.assertRaises(Exception):
            self.env['product.vendor.update'].create({})

    def test_wizard_form_view_loads(self):
        with Form(self.env['product.vendor.update']) as form:
            form.partner_id = self.vendor
            form.lead_time = 3
            self.assertEqual(form.lead_time, 3)

    # ------------------------------------------------------------------
    # action_update_vendor
    # ------------------------------------------------------------------
    def test_update_single_product_all_fields(self):
        self._run_wizard(
            self.product_1,
            lead_time=7,
            quantity=10,
            price_unit=25.5,
            validity_from=date(2026, 1, 1),
            validity_to=date(2026, 12, 31),
            vendor_product_name='Vendor Name X',
            vendor_product_code='VX-001',
        )
        seller = self.product_1.seller_ids
        self.assertEqual(len(seller), 1)
        self.assertEqual(seller.partner_id, self.vendor)
        self.assertEqual(seller.delay, 7)
        self.assertEqual(seller.min_qty, 10)
        self.assertAlmostEqual(seller.price, 25.5)
        self.assertEqual(seller.currency_id, self.env.company.currency_id)
        self.assertEqual(seller.date_start, date(2026, 1, 1))
        self.assertEqual(seller.date_end, date(2026, 12, 31))
        self.assertEqual(seller.product_name, 'Vendor Name X')
        self.assertEqual(seller.product_code, 'VX-001')
        self.assertEqual(seller.product_tmpl_id, self.product_1)

    def test_update_multiple_products(self):
        self._run_wizard(self.products, price_unit=12.0, lead_time=4)
        for product in self.products:
            self.assertEqual(len(product.seller_ids), 1, product.name)
            self.assertEqual(product.seller_ids.partner_id, self.vendor)
            self.assertAlmostEqual(product.seller_ids.price, 12.0)
            self.assertEqual(product.seller_ids.delay, 4)

    def test_update_only_affects_selected_products(self):
        self._run_wizard(self.product_1 | self.product_2, price_unit=5.0)
        self.assertEqual(len(self.product_1.seller_ids), 1)
        self.assertEqual(len(self.product_2.seller_ids), 1)
        self.assertFalse(self.product_3.seller_ids)

    def test_update_keeps_existing_vendors(self):
        self.env['product.supplierinfo'].create({
            'partner_id': self.vendor_b.id,
            'product_tmpl_id': self.product_1.id,
            'price': 99.0,
        })
        self._run_wizard(self.product_1, price_unit=10.0)
        self.assertEqual(len(self.product_1.seller_ids), 2)
        self.assertEqual(
            self.product_1.seller_ids.mapped('partner_id'),
            self.vendor | self.vendor_b)

    def test_update_with_foreign_currency(self):
        # Only the company currency is active in a fresh test database, so
        # look among inactive currencies too and activate one.
        other = self.env['res.currency'].with_context(
            active_test=False).search(
            [('id', '!=', self.env.company.currency_id.id)], limit=1)
        self.assertTrue(other)
        other.active = True
        self._run_wizard(self.product_1, currency_id=other.id, price_unit=3.0)
        self.assertEqual(self.product_1.seller_ids.currency_id, other)

    def test_running_wizard_twice_creates_two_lines(self):
        self._run_wizard(self.product_1, price_unit=1.0)
        self._run_wizard(self.product_1, price_unit=2.0)
        self.assertEqual(len(self.product_1.seller_ids), 2)
        self.assertEqual(
            sorted(self.product_1.seller_ids.mapped('price')), [1.0, 2.0])

    def test_update_with_empty_active_ids_creates_nothing(self):
        before = self.env['product.supplierinfo'].search_count([])
        wizard = self._create_wizard().with_context(active_ids=[])
        wizard.action_update_vendor()
        self.assertEqual(
            self.env['product.supplierinfo'].search_count([]), before)

    # ------------------------------------------------------------------
    # onchange validity dates
    # ------------------------------------------------------------------
    def test_onchange_validity_to_before_from_raises(self):
        wizard = self.env['product.vendor.update'].new({
            'partner_id': self.vendor.id,
            'validity_from': date(2026, 6, 1),
            'validity_to': date(2026, 1, 1),
        })
        with self.assertRaises(ValidationError):
            wizard._onchange_validity_to()

    def test_onchange_validity_to_after_from_ok(self):
        wizard = self.env['product.vendor.update'].new({
            'partner_id': self.vendor.id,
            'validity_from': date(2026, 1, 1),
            'validity_to': date(2026, 6, 1),
        })
        wizard._onchange_validity_to()  # must not raise

    def test_onchange_validity_same_day_ok(self):
        wizard = self.env['product.vendor.update'].new({
            'partner_id': self.vendor.id,
            'validity_from': date(2026, 3, 1),
            'validity_to': date(2026, 3, 1),
        })
        wizard._onchange_validity_to()  # must not raise

    def test_onchange_validity_to_without_from(self):
        """Setting only 'Validity To' should not crash.

        NOTE: with the current implementation `date < False` raises a
        TypeError, so this test is expected to FAIL until the onchange is
        guarded with `if self.validity_to and self.validity_from and ...`.
        """
        wizard = self.env['product.vendor.update'].new({
            'partner_id': self.vendor.id,
            'validity_to': date(2026, 3, 1),
        })
        wizard._onchange_validity_to()

    # ------------------------------------------------------------------
    # access rights
    # ------------------------------------------------------------------
    def test_purchase_user_can_use_wizard(self):
        user = new_test_user(
            self.env, login='pmvu_purchase_user',
            groups='base.group_user,purchase.group_purchase_user')
        wizard = self.env['product.vendor.update'].with_user(user).create(
            {'partner_id': self.vendor.id, 'price_unit': 8.0})
        wizard.with_context(
            active_ids=self.product_1.ids).action_update_vendor()
        self.env.invalidate_all()
        self.assertEqual(len(self.product_1.seller_ids), 1)

    def test_portal_user_cannot_use_wizard(self):
        user = new_test_user(
            self.env, login='pmvu_portal_user', groups='base.group_portal')
        with self.assertRaises(AccessError):
            self.env['product.vendor.update'].with_user(user).create(
                {'partner_id': self.vendor.id})