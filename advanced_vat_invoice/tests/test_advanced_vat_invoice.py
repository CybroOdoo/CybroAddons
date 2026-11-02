# -*- coding: utf-8 -*-
###############################################################################
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
################################################################################
from datetime import datetime
from os.path import exists, join
from unittest.mock import patch

import pytz

from odoo.exceptions import UserError
from odoo.modules.module import get_module_path
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAdvancedVatInvoice(TransactionCase):
    """Test suite verifying Saudi VAT invoice reports, QR code computation,
    and settings configuration.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module_path = get_module_path('advanced_vat_invoice')
        cls.company = cls.env.company
        cls.company.vat = '310123456700003'
        cls.sar_currency = cls.env.ref('base.SAR')

    def test_01_module_installed(self):
        """Verify advanced_vat_invoice module is installed."""
        module = self.env['ir.module.module'].search(
            [('name', '=', 'advanced_vat_invoice')], limit=1
        )
        self.assertTrue(module, 'Module record not found')
        self.assertEqual(
            module.state, 'installed', 'Module should be in installed state'
        )

    def test_02_manifest_metadata(self):
        """Verify manifest metadata meets checklist standards."""
        module = self.env['ir.module.module'].search(
            [('name', '=', 'advanced_vat_invoice')], limit=1
        )
        self.assertEqual(module.license, 'LGPL-3')
        self.assertEqual(module.category_id.name, 'Accounting')
        dep_names = module.dependencies_id.mapped('name')
        self.assertIn('account', dep_names)
        self.assertNotIn('account_payment', dep_names)

    def test_03_res_config_settings(self):
        """Verify res.config.settings get and set values for QR code."""
        settings = self.env['res.config.settings'].create({
            'is_qr': True,
            'generate_qr': 'manually',
        })
        settings.set_values()
        vals = settings.get_values()
        self.assertTrue(vals.get('is_qr'))
        self.assertEqual(vals.get('generate_qr'), 'manually')

        settings.write({
            'generate_qr': 'automatically',
        })
        settings.set_values()
        vals = settings.get_values()
        self.assertEqual(vals.get('generate_qr'), 'automatically')

    def test_04_account_move_qr_computation(self):
        """Verify qr_button and qr_page field computation on account.move."""
        param = self.env['ir.config_parameter'].sudo()
        param.set_bool('advanced_vat_invoice.is_qr', True)
        param.set_str('advanced_vat_invoice.generate_qr', 'manually')

        partner = self.env['res.partner'].create({
            'name': 'Test Saudi Partner',
            'vat': '300000000000003',
        })
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
        })
        move._compute_qr()
        self.assertTrue(move.qr_button)
        self.assertFalse(move.qr_page)

        param.set_str('advanced_vat_invoice.generate_qr', 'automatically')
        move._compute_qr()
        self.assertFalse(move.qr_button)
        self.assertTrue(move.qr_page)

    def test_05_qr_generation_methods(self):
        """Verify hex encoding and QR code generation on account.move."""
        partner = self.env['res.partner'].create({
            'name': 'Test Saudi Customer',
            'vat': '310000000000003',
        })
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_date': datetime(2026, 10, 28).date(),
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Consulting Service',
                    'price_unit': 200.0,
                    'quantity': 1.0,
                }),
            ],
            'create_date': datetime(2026, 10, 28, 12, 0, 0),
        })

        # Test helper functions
        hex_val = move.string_hexa('Cybrosys')
        self.assertTrue(hex_val)
        empty_hex = move.string_hexa(False)
        self.assertEqual(empty_hex, "")

        tagged_hex = move.hexa("01", "08", "Cybrosys")
        self.assertTrue(tagged_hex.startswith("01"))
        empty_tagged = move.hexa(False, False, False)
        self.assertEqual(empty_tagged, "")

        # Test timezone handling with no user tz (simulating fresh DB)
        self.env.user.tz = False
        tz_res = move.timezone(datetime(2026, 10, 28, 12, 0, 0))
        self.assertTrue(tz_res)

        # Test timezone with empty date (defaults to now)
        tz_now = move.timezone(False)
        self.assertTrue(tz_now)

        # Test timezone with custom or invalid context tz
        move_bad_tz = move.with_context(tz='Invalid/Timezone')
        self.assertTrue(move_bad_tz.timezone(datetime(2026, 10, 28, 12, 0, 0)))

        # Test timezone with timezone-aware datetime
        tz_aware = pytz.timezone('Asia/Riyadh').localize(
            datetime(2026, 10, 28, 15, 0, 0)
        )
        self.assertTrue(move.timezone(tz_aware))

        # Test QR code data payload
        qr_data = move.qr_code_data()
        self.assertTrue(qr_data)

        # Test manual generation
        param = self.env['ir.config_parameter'].sudo()
        param.set_str('advanced_vat_invoice.generate_qr', 'manually')
        move.generate_qr_button()
        self.assertTrue(move.qr)

        # Test automatic generation logic on invoice posting
        param.set_str('advanced_vat_invoice.generate_qr', 'automatically')
        move.qr = False
        move.action_post()
        self.assertEqual(move.state, 'posted')
        self.assertTrue(move.qr)

        # Test multi-record execution (verify no singleton error on move recordset)
        move2 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_date': datetime(2026, 10, 28).date(),
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Additional Line',
                    'price_unit': 50.0,
                    'quantity': 2.0,
                }),
            ],
            'create_date': datetime(2026, 10, 28, 12, 0, 0),
        })
        param.set_str('advanced_vat_invoice.generate_qr', 'manually')
        moves = move | move2
        moves.generate_qr_button()
        self.assertTrue(move2.qr)

        # Test that manual QR is preserved on recompute
        qr_saved = move.qr
        move._compute_qr_code()
        self.assertEqual(
            move.qr, qr_saved, "Manual QR should be preserved on recompute"
        )

        # Test error handling when qrcode is unavailable
        with patch('odoo.addons.advanced_vat_invoice.models.account_move.qrcode', None):
            param.set_str('advanced_vat_invoice.generate_qr', 'manually')
            with self.assertRaises(UserError):
                move.generate_qr_button()
            param.set_str('advanced_vat_invoice.generate_qr', 'automatically')
            move.qr = False
            with self.assertRaises(UserError):
                move._compute_qr_code()

    def test_06_reports_action_definitions(self):
        """Verify all report actions exist and match account.move."""
        report_ids = [
            'advanced_vat_invoice.action_report_vat_report',
            'advanced_vat_invoice.action_vat_invoice',
            'advanced_vat_invoice.action_report_simplified_report',
            'advanced_vat_invoice.action_tax_invoice',
        ]
        for xml_id in report_ids:
            report = self.env.ref(xml_id, raise_if_not_found=False)
            self.assertIsNotNone(report, f'Report action {xml_id} must exist')
            self.assertEqual(report.model, 'account.move')
            self.assertEqual(report.report_type, 'qweb-pdf')

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

        for i in range(1, 8):
            screenshot = join(
                self.module_path,
                'static',
                'description',
                'assets',
                'screenshots',
                f'S0{i}.png',
            )
            self.assertTrue(
                exists(screenshot), f'Missing screenshot S0{i}.png'
            )

    def test_08_render_report_templates(self):
        """Verify rendering of both VAT and Simplified Tax invoice reports."""
        partner = self.env['res.partner'].create({
            'name': 'Test Saudi Customer Report',
            'vat': '310000000000003',
        })
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_date': datetime(2026, 10, 28).date(),
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Test Product Service',
                    'price_unit': 100.0,
                    'quantity': 1.0,
                }),
            ],
        })
        move.action_post()
        # Generate QR code manually
        param = self.env['ir.config_parameter'].sudo()
        param.set_str('advanced_vat_invoice.generate_qr', 'manually')
        move.generate_qr_button()

        # Render VAT Invoice template
        rendered_vat = self.env['ir.ui.view']._render_template(
            'advanced_vat_invoice.vat_template',
            {'docs': move, 'doc': move, 'o': move},
        )
        self.assertTrue(rendered_vat)
        self.assertIn('فاتورة ضريبية', rendered_vat)
        self.assertIn('VAT Invoice', rendered_vat)
        self.assertIn('تاريخ إصدار الفاتورة', rendered_vat)
        self.assertIn('Taxable Amount', rendered_vat)
        self.assertIn('الرقم الضريبي', rendered_vat)
        self.assertNotIn('ظريبه الشراء', rendered_vat)

        # Render Simplified Tax Invoice template
        rendered_simp = self.env['ir.ui.view']._render_template(
            'advanced_vat_invoice.simplified_tax_template',
            {'docs': move, 'doc': move, 'o': move},
        )
        self.assertTrue(rendered_simp)
        self.assertIn('فاتورة ضريبية مبسطة', rendered_simp)
        self.assertIn('Simplified Tax Invoice', rendered_simp)

        # Verify reports render without crashing when invoice has no QR code
        # (qr is False)
        move_no_qr = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
        })
        templates = [
            'advanced_vat_invoice.vat_template',
            'advanced_vat_invoice.simplified_tax_template',
        ]
        for tmpl in templates:
            rendered_no_qr = self.env['ir.ui.view']._render_template(
                tmpl,
                {'docs': move_no_qr, 'doc': move_no_qr, 'o': move_no_qr},
            )
            self.assertTrue(rendered_no_qr)
