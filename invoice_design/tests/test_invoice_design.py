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
from odoo.exceptions import AccessError, UserError
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import new_test_user, tagged
from odoo.tools import mute_logger

TEMPLATE = '<div><t t-out="invoice.name"/> CUSTOM-DESIGN-MARKER</div>'


@tagged('post_install', '-at_install')
class TestInvoiceDesign(AccountTestInvoicingCommon):
    """Tests for the invoice.design model, settings and report."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Without a report layout, report_action() returns the layout
        # configuration wizard instead of the report action.
        cls.env.company.external_report_layout_id = cls.env.ref(
            'web.external_layout_standard')
        cls.Design = cls.env['invoice.design']
        cls.design = cls.Design.create({
            'name': 'Test Design',
            'invoice_template': TEMPLATE,
        })
        cls.invoice = cls.init_invoice(
            'out_invoice', products=cls.product_a, post=True)

    def _enable_custom_invoice(self, design=None):
        params = self.env['ir.config_parameter'].sudo()
        params.set_str('invoice_design.is_custom_invoice', 'True')
        params.set_str('invoice_design.invoice_design',
                       str((design or self.design).id))

    # ------------------------------------------------------------------
    # invoice.design model
    # ------------------------------------------------------------------
    def test_create_builds_qweb_view(self):
        view = self.design.view_id
        self.assertTrue(view)
        self.assertEqual(view.type, 'qweb')
        self.assertEqual(view.key, 'account.Test Design')
        self.assertEqual(view.arch_db, TEMPLATE)

    def test_create_uses_default_template(self):
        design = self.Design.create({'name': 'Default Template Design'})
        self.assertIn('Enter your code here', design.invoice_template)
        self.assertTrue(design.view_id)

    def test_create_invalid_xml_raises(self):
        with self.assertRaises(UserError):
            self.Design.create({
                'name': 'Broken',
                'invoice_template': '<div><p></div>',
            })
        self.assertFalse(self.Design.search([('name', '=', 'Broken')]))

    def test_name_is_unique(self):
        with self.assertRaises(Exception), mute_logger('odoo.sql_db'):
            with self.cr.savepoint():
                self.Design.create({'name': 'Test Design',
                                    'invoice_template': TEMPLATE})

    def test_write_syncs_view(self):
        self.design.write({'name': 'Renamed',
                           'invoice_template': '<div>New</div>'})
        view = self.design.view_id
        self.assertEqual(view.name, 'Renamed')
        self.assertEqual(view.key, 'account.Renamed')
        self.assertEqual(view.arch_db, '<div>New</div>')

    def test_write_invalid_xml_raises(self):
        with self.assertRaises(UserError):
            self.design.write({'invoice_template': '<div>'})
        self.assertEqual(self.design.view_id.arch_db, TEMPLATE)

    def test_unlink_removes_view(self):
        view = self.design.view_id
        self.design.unlink()
        self.assertFalse(view.exists())

    def test_regular_user_cannot_edit_designs(self):
        user = new_test_user(self.env, login='plain_design_user',
                             groups='base.group_user')
        with self.assertRaises(AccessError):
            self.Design.with_user(user).create({
                'name': 'Not Allowed', 'invoice_template': TEMPLATE})

    # ------------------------------------------------------------------
    # settings
    # ------------------------------------------------------------------
    def test_settings_store_config_parameters(self):
        settings = self.env['res.config.settings'].create({
            'is_custom_invoice': True,
            'invoice_design_id': self.design.id,
        })
        settings.execute()
        params = self.env['ir.config_parameter'].sudo()
        self.assertTrue(params.get_str('invoice_design.is_custom_invoice'))
        self.assertEqual(params.get_str('invoice_design.invoice_design'),
                         str(self.design.id))

    # ------------------------------------------------------------------
    # printing
    # ------------------------------------------------------------------
    def test_print_requires_custom_invoice_enabled(self):
        self.env['ir.config_parameter'].sudo().set_str(
            'invoice_design.is_custom_invoice', '')
        with self.assertRaises(UserError):
            self.invoice.action_print_custom_invoice()

    def test_print_requires_selected_design(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_str('invoice_design.is_custom_invoice', 'True')
        params.set_str('invoice_design.invoice_design', '')
        with self.assertRaises(UserError):
            self.invoice.action_print_custom_invoice()

    def test_print_returns_report_action(self):
        self._enable_custom_invoice()
        action = self.invoice.action_print_custom_invoice()
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_name'],
                         'invoice_design.report_invoice_design')

    def test_report_data(self):
        self._enable_custom_invoice()
        data = self.invoice._get_custom_invoice_report_data()
        self.assertEqual(data['key'], self.design.view_id.key)
        self.assertEqual(data['move_ids'], self.invoice.ids)

    def test_report_renders_design(self):
        self._enable_custom_invoice()
        data = self.invoice._get_custom_invoice_report_data()
        html, _report_type = self.env['ir.actions.report']._render_qweb_html(
            'invoice_design.report_invoice_design', [], data=data)
        content = html.decode()
        self.assertIn('CUSTOM-DESIGN-MARKER', content)
        self.assertIn(self.invoice.name, content)

    def test_demo_design_is_installed(self):
        demo = self.env.ref('invoice_design.invoice_design_demo')
        self.assertTrue(demo.view_id)
