# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from os.path import exists, join

from odoo.modules.module import get_module_path
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'invoice_format_editor')
class TestInvoiceFormatEditor(TransactionCase):
    """Test suite verifying invoice format editor models, configuration,
    and preview functionality.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module_path = get_module_path('invoice_format_editor')

    def test_01_module_installed(self):
        """Verify invoice_format_editor module is installed."""
        module = self.env['ir.module.module'].search(
            [('name', '=', 'invoice_format_editor')], limit=1
        )
        self.assertTrue(module, 'Module record not found')
        self.assertEqual(
            module.state, 'installed', 'Module should be in installed state'
        )

    def test_02_manifest_metadata(self):
        """Verify manifest metadata meets checklist standards."""
        module = self.env['ir.module.module'].search(
            [('name', '=', 'invoice_format_editor')], limit=1
        )
        self.assertEqual(module.license, 'LGPL-3')
        self.assertEqual(module.category_id.name, 'Accounting')
        dep_names = module.dependencies_id.mapped('name')
        self.assertIn('account', dep_names)
        self.assertIn('web', dep_names)
        self.assertIn('sale_management', dep_names)

    def test_03_doc_layout_crud(self):
        """Verify doc.layout creation, field persistence, and updates."""
        layout = self.env['doc.layout'].create({
            'name': 'Custom Modern Layout',
            'base_color': '#336699',
            'heading_text_color': '#ffffff',
            'text_color': '#111111',
            'customer_text_color': '#222222',
            'company_text_color': '#333333',
            'logo_position': 'left',
            'tagline_position': 'right',
            'customer_position': 'left',
            'company_position': 'right',
            'sales_person': True,
            'description': True,
            'tax_value': True,
            'reference': True,
            'source': False,
            'address': True,
            'city': True,
            'country': True,
            'vat': True,
        })
        self.assertTrue(layout.id, 'Layout should have a valid ID')
        self.assertEqual(layout.name, 'Custom Modern Layout')
        self.assertEqual(layout.logo_position, 'left')
        layout.write({'sales_person': False, 'source': True})
        self.assertFalse(layout.sales_person)
        self.assertTrue(layout.source)

    def test_04_company_layout_configuration(self):
        """Verify company document layout configuration and relation."""
        company = self.env.company
        layout = self.env['doc.layout'].create({
            'name': 'Company Theme Layout',
            'base_color': '#445566',
        })
        company.write({
            'base_layout': 'modern',
            'document_layout_id': layout.id,
        })
        self.assertEqual(company.base_layout, 'modern')
        self.assertEqual(company.document_layout_id, layout)

    def test_05_account_move_theme(self):
        """Verify account.move relates theme_id to company document layout."""
        partner = self.env['res.partner'].create({
            'name': 'Test Invoice Partner',
        })
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
        })
        self.assertEqual(move.theme_id, self.env.company.document_layout_id)

    def test_06_base_document_layout_wizard(self):
        """Verify base.document.layout wizard preview and euro format."""
        layout = self.env['doc.layout'].create({
            'name': 'Wizard Preview Theme',
            'address': True,
        })
        self.env.company.document_layout_id = layout.id
        report_layout = self.env['report.layout'].search([], limit=1)
        wizard = self.env['base.document.layout'].create({
            'report_layout_id': report_layout.id if report_layout else False,
            'document_layout_id': layout.id,
        })
        expected_templates = {
            'normal': 'invoice_format_editor.report_preview_normal',
            'modern': 'invoice_format_editor.report_preview_modern',
            'old': 'invoice_format_editor.report_preview_old',
            'default': 'web.report_invoice_wizard_preview',
        }
        for mode, expected_tmpl in expected_templates.items():
            wizard.base_layout = mode
            self.assertEqual(wizard._get_preview_template(), expected_tmpl)
            wizard._compute_preview()
            if wizard.report_layout_id:
                self.assertTrue(wizard.preview)
                if mode == 'normal':
                    self.assertIn('Deco Addict', wizard.preview)
                elif mode in ('modern', 'old'):
                    self.assertIn('INV/2021/07/0003', wizard.preview)

        wizard.base_layout = False
        wizard._compute_preview()
        self.assertFalse(wizard.preview)

        wizard.report_layout_id = False
        wizard._compute_preview()
        self.assertFalse(wizard.preview)

        euro_pf = self.env.ref(
            'base.paperformat_euro', raise_if_not_found=False
        )
        if euro_pf:
            wizard.paperformat_id = euro_pf
            wizard._compute_is_euro_paperformat()
            self.assertTrue(wizard.is_euro_paperformat)
            wizard.base_layout = 'modern'
            wizard._onchange_paperformat_id()
            self.assertEqual(wizard.base_layout, 'default')

    def test_07_docs_and_assets(self):
        """Verify required documentation and asset files exist."""
        required_relative_paths = [
            'README.rst',
            join('doc', 'RELEASE_NOTES.md'),
            join('static', 'description', 'icon.png'),
            join('static', 'description', 'banner.jpg'),
            join('static', 'description', 'index.html'),
        ]
        for rel_path in required_relative_paths:
            full_path = join(self.module_path, rel_path)
            self.assertTrue(
                exists(full_path), f'Missing required file: {rel_path}'
            )

        for i in range(1, 7):
            screenshot = join(
                self.module_path,
                'static',
                'description',
                'assets',
                'screenshots',
                f'{i}.png',
            )
            self.assertTrue(
                exists(screenshot), f'Missing screenshot {i}.png'
            )

    def test_08_doc_layout_access_rights(self):
        """Verify base.group_user has read access ('r') and
        account.group_account_manager has full CRUD ('crud') on doc.layout.
        """
        access_user = self.env.ref(
            'invoice_format_editor.access_doc_layout_user',
            raise_if_not_found=False,
        )
        self.assertTrue(access_user, 'User access record should exist')
        self.assertEqual(access_user.group_id, self.env.ref('base.group_user'))
        self.assertEqual(access_user.operation, 'r')

        access_mgr = self.env.ref(
            'invoice_format_editor.access_doc_layout_manager',
            raise_if_not_found=False,
        )
        self.assertTrue(access_mgr, 'Manager access record should exist')
        self.assertEqual(
            access_mgr.group_id, self.env.ref('account.group_account_manager')
        )
        self.assertEqual(access_mgr.operation, 'crud')

    def test_09_invoice_report_templates(self):
        """Verify rendering of invoice report templates (normal, modern, old)."""
        partner = self.env['res.partner'].create({
            'name': 'Test Invoice Customer',
            'street': 'Main Street 10',
            'city': 'Metropolis',
        })
        layout = self.env['doc.layout'].create({
            'name': 'Report Test Layout',
            'base_color': '#224466',
            'customer_text_color': '#112233',
            'source': True,
            'address': True,
            'city': True,
        })
        self.env.company.write({
            'document_layout_id': layout.id,
        })
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_date': '2026-10-30',
            'invoice_line_ids': [
                (0, 0, {'name': 'Service Item', 'quantity': 1, 'price_unit': 250.0}),
            ],
        })
        templates = (
            'invoice_format_editor.custom_template_report_invoice_normal',
            'invoice_format_editor.custom_template_report_invoice_modern',
            'invoice_format_editor.old_std_report_invoice_document',
        )
        # Test Draft Invoice rendering
        for tmpl in templates:
            rendered = self.env['ir.ui.view']._render_template(
                tmpl,
                {'docs': move, 'o': move, 'company': self.env.company},
            )
            self.assertTrue(rendered)
            self.assertIn('Draft Invoice', rendered)
            self.assertNotIn('style="color:#{', rendered)
            self.assertIn('color:#112233 !important;', rendered)

        # Post invoice and verify heading switches to Invoice
        move.action_post()
        for tmpl in templates:
            rendered = self.env['ir.ui.view']._render_template(
                tmpl,
                {'docs': move, 'o': move, 'company': self.env.company},
            )
            self.assertTrue(rendered)
            self.assertIn('Invoice', rendered)
            self.assertNotIn('Draft Invoice', rendered)
