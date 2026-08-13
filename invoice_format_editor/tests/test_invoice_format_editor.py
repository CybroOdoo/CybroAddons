# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestInvoiceFormatEditor(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.doc_layout = cls.env['doc.layout'].create({
            'name': 'Test Layout',
            'base_color': '112233',
            'heading_text_color': '445566',
            'text_color': '778899',
            'customer_text_color': 'AABBCC',
            'company_text_color': 'DDEEFF',
            'logo_position': 'left',
            'tagline_position': 'right',
            'customer_position': 'left',
            'company_position': 'right',
        })
        cls.company.write({
            'base_layout': 'modern',
            'document_layout_id': cls.doc_layout.id,
        })
        cls.preview_view = cls.env['ir.ui.view'].create({
            'name': 'invoice_format_editor_test_preview',
            'type': 'qweb',
            'arch': '<t t-name="invoice_format_editor.test_preview"></t>',
        })
        cls.report_layout = cls.env['report.layout'].create({
            'name': 'Invoice Format Editor Test Layout',
            'view_id': cls.preview_view.id,
        })

    def _log_test_start(self):
        _logger.info("Starting %s", self._testMethodName)

    def _log_test_complete(self):
        _logger.info("Completed %s", self._testMethodName)

    def test_account_move_related_layout_fields(self):
        self._log_test_start()
        move = self.env['account.move'].new({
            'company_id': self.company.id,
        })

        self.assertEqual(move.base_layout, 'default')
        self.assertEqual(move.theme_id, self.doc_layout)
        self._log_test_complete()

    def test_document_layout_wizard_related_fields(self):
        self._log_test_start()
        wizard = self.env['base.document.layout'].new({
            'company_id': self.company.id,
        })

        self.assertEqual(wizard.base_layout, 'modern')
        self.assertEqual(wizard.document_layout_id, self.doc_layout)
        self._log_test_complete()

    def test_compute_preview_uses_expected_template(self):
        self._log_test_start()
        template_map = {
            'default': 'web.report_invoice_wizard_preview',
            'normal': 'invoice_format_editor.report_preview_normal',
            'modern': 'invoice_format_editor.report_preview_modern',
            'old': 'invoice_format_editor.report_preview_old',
        }

        with patch.object(type(self.env['base.document.layout']), '_get_asset_style', return_value=''):
            with patch.object(type(self.env['ir.ui.view']), '_render_template', autospec=True, return_value='<div>preview</div>') as render_template:
                for base_layout, template in template_map.items():
                    wizard = self.env['base.document.layout'].new({
                        'company_id': self.company.id,
                        'base_layout': base_layout,
                        'report_layout_id': self.report_layout.id,
                    })

                    wizard._compute_preview()

                    self.assertEqual(wizard.preview, '<div>preview</div>')
                    self.assertEqual(render_template.call_args[0][1], template)
        self._log_test_complete()

    def test_compute_preview_returns_false_without_report_layout(self):
        self._log_test_start()
        wizard = self.env['base.document.layout'].new({
            'company_id': self.company.id,
            'base_layout': 'modern',
        })

        wizard._compute_preview()

        self.assertFalse(wizard.preview)
        self._log_test_complete()

    def test_compute_preview_returns_false_on_render_error(self):
        self._log_test_start()
        wizard = self.env['base.document.layout'].new({
            'company_id': self.company.id,
            'base_layout': 'modern',
            'report_layout_id': self.report_layout.id,
        })

        with patch.object(type(self.env['base.document.layout']), '_get_asset_style', return_value=''):
            with patch.object(type(self.env['ir.ui.view']), '_render_template', autospec=True, side_effect=Exception('render failure')):
                wizard._compute_preview()

        self.assertFalse(wizard.preview)
        self._log_test_complete()

    def test_onchange_paperformat_resets_base_layout_for_euro_format(self):
        self._log_test_start()
        wizard = self.env['base.document.layout'].new({
            'company_id': self.company.id,
            'base_layout': 'old',
        })
        wizard.paperformat_id = self.env.ref('base.paperformat_euro')

        wizard._onchange_paperformat_id()

        self.assertEqual(wizard.base_layout, 'default')
        self._log_test_complete()

    def test_onchange_paperformat_keeps_layout_for_other_formats(self):
        self._log_test_start()
        wizard = self.env['base.document.layout'].new({
            'company_id': self.company.id,
            'base_layout': 'normal',
        })
        wizard.paperformat_id = self.env.ref('base.paperformat_us')

        wizard._onchange_paperformat_id()

        self.assertEqual(wizard.base_layout, 'normal')
        self._log_test_complete()