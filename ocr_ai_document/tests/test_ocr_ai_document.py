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
import base64
import datetime
import json
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase

# Minimal 1x1 PNG, valid base64 payload for file_upload tests.
PNG_B64 = (
    b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42'
    b'YAAAAASUVORK5CYII='
)



# ==========================================================================
# Config models: odoo.ocr.api.config / odoo.ocr.ai.config / odoo.ocr.ai.config.line
# ==========================================================================

class TestOcrApiConfig(TransactionCase):
    """Tests for odoo.ocr.api.config (per-company fynix.ai credentials)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ApiConfig = cls.env['odoo.ocr.api.config']
        cls.company = cls.env.company

    def test_create_config(self):
        config = self.ApiConfig.create({
            'company_id': self.company.id,
            'api_key': 'test-token-123',
        })
        self.assertEqual(config.server_url, 'https://ai.fynix.app/tus_ocr_api')
        self.assertEqual(config.date_format, '%d-%m-%y')

    def test_unique_company_constraint(self):
        self.ApiConfig.create({
            'company_id': self.company.id,
            'api_key': 'token-a',
        })
        with self.assertRaises(ValidationError):
            self.ApiConfig.create({
                'company_id': self.company.id,
                'api_key': 'token-b',
            })

    def test_action_test_connection_requires_server_url(self):
        config = self.ApiConfig.new({
            'company_id': self.company.id,
            'api_key': 'token-a',
            'server_url': False,
        })
        with self.assertRaises(UserError):
            config.action_test_connection()

    def test_action_test_connection_strips_endpoint_path(self):
        config = self.ApiConfig.create({
            'company_id': self.company.id,
            'api_key': 'token-a',
            'server_url': 'https://ai.fynix.app/tus_ocr_api',
        })
        action = config.action_test_connection()
        self.assertEqual(action['url'], 'https://ai.fynix.app')
        self.assertEqual(action['type'], 'ir.actions.act_url')


@tagged('post_install', '-at_install')
class TestOcrAiConfig(TransactionCase):
    """Tests for odoo.ocr.ai.config / odoo.ocr.ai.config.line (field mapping)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.IrModel = cls.env['ir.model']
        cls.IrModelFields = cls.env['ir.model.fields']
        cls.Config = cls.env['odoo.ocr.ai.config']
        cls.ConfigLine = cls.env['odoo.ocr.ai.config.line']

        cls.po_model = cls.IrModel.search([('model', '=', 'purchase.order')], limit=1)
        cls.po_model.is_ocr_tus = True

        cls.field_partner_id = cls.IrModelFields.search([
            ('model', '=', 'purchase.order'), ('name', '=', 'partner_id'),
        ], limit=1)
        cls.field_order_line = cls.IrModelFields.search([
            ('model', '=', 'purchase.order'), ('name', '=', 'order_line'),
        ], limit=1)
        cls.field_notes = cls.IrModelFields.search([
            ('model', '=', 'purchase.order'), ('name', '=', 'notes'),
        ], limit=1)
        cls.field_line_product_id = cls.IrModelFields.search([
            ('model', '=', 'purchase.order.line'), ('name', '=', 'product_id'),
        ], limit=1)

    def test_is_ocr_tus_domain_filters_model_selection(self):
        """Only models flagged is_ocr_tus should be selectable as model_id."""
        self.assertTrue(self.po_model.is_ocr_tus)
        untouched_model = self.IrModel.search([('model', '=', 'res.partner')], limit=1)
        self.assertFalse(untouched_model.is_ocr_tus)

    def test_unique_active_model_constraint(self):
        self.Config.create({'model_id': self.po_model.id, 'active': True})
        with self.assertRaises(ValidationError):
            self.Config.create({'model_id': self.po_model.id, 'active': True})

    def test_inactive_duplicate_allowed(self):
        self.Config.create({'model_id': self.po_model.id, 'active': True})
        inactive = self.Config.create({'model_id': self.po_model.id, 'active': False})
        self.assertTrue(inactive)

    def test_onchange_model_id_clears_lines(self):
        config = self.Config.create({'model_id': self.po_model.id, 'active': True})
        config.model_ids = [(0, 0, {
            'title': 'Vendor',
            'ocr_field_id': self.field_partner_id.id,
        })]
        move_model = self.IrModel.search([('model', '=', 'account.move')], limit=1)
        move_model.is_ocr_tus = True

        with Form(config) as config_form:
            config_form.model_id = move_model
        self.assertFalse(config.model_ids)

    def test_one2many_requires_child_fields(self):
        config = self.Config.create({'model_id': self.po_model.id, 'active': True})
        with self.assertRaises(ValidationError):
            self.ConfigLine.create({
                'model_id': config.id,
                'title': 'Order Lines',
                'ocr_field_id': self.field_order_line.id,
                # ocr_ir_field_ids intentionally omitted
            })

    def test_one2many_with_child_fields_is_valid(self):
        config = self.Config.create({'model_id': self.po_model.id, 'active': True})
        line = self.ConfigLine.create({
            'model_id': config.id,
            'title': 'Order Lines',
            'ocr_field_id': self.field_order_line.id,
            'ocr_ir_field_ids': [(6, 0, [self.field_line_product_id.id])],
        })
        self.assertTrue(line)

    def test_many2one_does_not_require_child_fields(self):
        config = self.Config.create({'model_id': self.po_model.id, 'active': True})
        line = self.ConfigLine.create({
            'model_id': config.id,
            'title': 'Vendor',
            'ocr_field_id': self.field_partner_id.id,
        })
        self.assertTrue(line)

    def test_field_uniqueness_within_config(self):
        config = self.Config.create({'model_id': self.po_model.id, 'active': True})
        self.ConfigLine.create({
            'model_id': config.id,
            'title': 'Vendor',
            'ocr_field_id': self.field_partner_id.id,
        })
        with self.assertRaises(ValidationError):
            self.ConfigLine.create({
                'model_id': config.id,
                'title': 'Vendor Duplicate',
                'ocr_field_id': self.field_partner_id.id,
            })

    def test_same_field_allowed_in_different_configs(self):
        config_1 = self.Config.create({'model_id': self.po_model.id, 'active': True})
        move_model = self.IrModel.search([('model', '=', 'account.move')], limit=1)
        move_model.is_ocr_tus = True
        config_2 = self.Config.create({'model_id': move_model.id, 'active': True})

        self.ConfigLine.create({
            'model_id': config_1.id,
            'title': 'Vendor',
            'ocr_field_id': self.field_partner_id.id,
        })
        partner_field_move = self.IrModelFields.search([
            ('model', '=', 'account.move'), ('name', '=', 'partner_id'),
        ], limit=1)
        line_2 = self.ConfigLine.create({
            'model_id': config_2.id,
            'title': 'Customer',
            'ocr_field_id': partner_field_move.id,
        })
        self.assertTrue(line_2)

    def test_ocr_ir_field_ids_domain_for_relational_field(self):
        line = self.ConfigLine.new({
            'ocr_field_id': self.field_order_line.id,
        })
        line._compute_ocr_ir_field_ids_domain()
        line_model = self.IrModel.search(
            [('model', '=', 'purchase.order.line')], limit=1)
        self.assertEqual(
            line.ocr_ir_field_ids_domain,
            str([
                ('model_id', '=', line_model.id),
                ('ttype', 'in', [
                    'char', 'date', 'integer', 'selection', 'monetary',
                    'float', 'one2many', 'text', 'many2many', 'many2one',
                ]),
            ]),
        )

    def test_ocr_ir_field_ids_domain_without_relation(self):
        line = self.ConfigLine.new({
            'ocr_field_id': self.field_notes.id,
        })
        line._compute_ocr_ir_field_ids_domain()
        self.assertEqual(line.ocr_ir_field_ids_domain, str([('model_id', '=', False)]))


# ==========================================================================
# import.via.ocr wizard + odoo.ocr.ai.mixin model extensions
# ==========================================================================

class TestImportViaOcrWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # This environment has another installed module that added a NOT NULL
        # constraint on product_template.publish_date. It's unrelated to this
        # module, but _find_product()'s Product.create() call trips over it,
        # so default it here for every recordset built from cls.env below.
        cls.env = cls.env(context=dict(
            cls.env.context, default_publish_date=fields.Datetime.now(),
        ))
        cls.IrModel = cls.env['ir.model']
        cls.IrModelFields = cls.env['ir.model.fields']
        cls.Config = cls.env['odoo.ocr.ai.config']
        cls.ConfigLine = cls.env['odoo.ocr.ai.config.line']
        cls.Wizard = cls.env['import.via.ocr']

        cls.env['odoo.ocr.api.config'].create({
            'company_id': cls.env.company.id,
            'api_key': 'test-token',
        })

        po_model = cls.IrModel.search([('model', '=', 'purchase.order')], limit=1)
        po_model.is_ocr_tus = True
        cls.po_config = cls.Config.create({
            'model_id': po_model.id,
            'active': True,
            'create_products_if_not_found': True,
        })

        def po_field(name):
            return cls.IrModelFields.search(
                [('model', '=', 'purchase.order'), ('name', '=', name)], limit=1)

        def po_line_field(name):
            return cls.IrModelFields.search(
                [('model', '=', 'purchase.order.line'), ('name', '=', name)], limit=1)

        cls.ConfigLine.create({
            'model_id': cls.po_config.id,
            'title': 'Vendor',
            'ocr_field_id': po_field('partner_id').id,
            'create_if_not_found': True,
        })
        cls.ConfigLine.create({
            'model_id': cls.po_config.id,
            'title': 'Reference',
            'ocr_field_id': po_field('partner_ref').id,
        })
        cls.ConfigLine.create({
            'model_id': cls.po_config.id,
            'title': 'Notes',
            'ocr_field_id': po_field('notes').id,
        })
        cls.ConfigLine.create({
            'model_id': cls.po_config.id,
            'title': 'Order Lines',
            'ocr_field_id': po_field('order_line').id,
            'ocr_ir_field_ids': [(6, 0, [
                po_line_field('product_id').id,
                po_line_field('name').id,
                po_line_field('product_qty').id,
                po_line_field('price_unit').id,
            ])],
        })

    def _make_wizard(self, response_dict, config=None):
        attachment = self.env['ir.attachment'].create({
            'name': 'test_invoice.pdf',
            'mimetype': 'application/pdf',
            'datas': base64.b64encode(b'%PDF-1.4 fake content'),
        })
        wizard = self.Wizard.create({
            'file_upload': base64.b64encode(b'%PDF-1.4 fake content'),
            'file_upload_name': 'test_invoice.pdf',
            'ocr_config_id': (config or self.po_config).id,
            'ocr_attachment_id': attachment.id,
            'ocr_response_received': True,
            'response_text': json.dumps(response_dict),
        })
        return wizard

    # ------------------------------------------------------------------
    # File validation / computed fields
    # ------------------------------------------------------------------

    def test_file_format_accepts_supported_extensions(self):
        wizard = self.Wizard.create({
            'file_upload': PNG_B64,
            'file_upload_name': 'scan.png',
        })
        self.assertTrue(wizard)

    def test_file_format_rejects_unsupported_extension(self):
        with self.assertRaises(ValidationError):
            self.Wizard.create({
                'file_upload': PNG_B64,
                'file_upload_name': 'scan.docx',
            })

    def test_compute_mime_type(self):
        wizard = self.Wizard.create({
            'file_upload': PNG_B64,
            'file_upload_name': 'scan.PNG',
        })
        self.assertEqual(wizard.mime_type, 'image/png')

    def test_compute_mime_type_no_file(self):
        wizard = self.Wizard.create({})
        self.assertFalse(wizard.mime_type)

    def test_onchange_file_upload_resets_response(self):
        wizard = self.Wizard.create({
            'file_upload_name': 'placeholder.png',
            'response_text': '{"foo": "bar"}',
            'ocr_response_received': True,
        })
        wizard.file_upload = PNG_B64
        wizard._onchange_file_upload()
        self.assertFalse(wizard.response_text)
        self.assertFalse(wizard.ocr_response_received)

    # ------------------------------------------------------------------
    # _parse_date
    # ------------------------------------------------------------------

    def test_parse_date_matches_configured_format(self):
        wizard = self.Wizard.create({})
        result = wizard._parse_date('25-12-25', '%d-%m-%y')
        self.assertEqual(result, datetime.date(2025, 12, 25))

    def test_parse_date_falls_back_to_iso_format(self):
        wizard = self.Wizard.create({})
        result = wizard._parse_date('2025-12-25', '%d-%m-%y')
        self.assertEqual(result, datetime.date(2025, 12, 25))

    def test_parse_date_invalid_returns_false(self):
        wizard = self.Wizard.create({})
        self.assertFalse(wizard._parse_date('not-a-date', '%d-%m-%y'))

    def test_parse_date_empty_returns_false(self):
        wizard = self.Wizard.create({})
        self.assertFalse(wizard._parse_date('', '%d-%m-%y'))

    # ------------------------------------------------------------------
    # _map_field_value: scalar types
    # ------------------------------------------------------------------

    def test_map_field_value_char_strips_whitespace(self):
        wizard = self.Wizard.create({})
        line = self.ConfigLine.search(
            [('model_id', '=', self.po_config.id), ('title', '=', 'Reference')], limit=1)
        self.assertEqual(
            wizard._map_field_value(line, '  PO-99  ', '%d-%m-%y', self.po_config),
            'PO-99',
        )

    def test_map_field_value_integer_valid(self):
        wizard = self.Wizard.create({})
        line = self.env['odoo.ocr.ai.config.line'].new({})
        line.ocr_field_id = self.IrModelFields.search(
            [('model', '=', 'purchase.order.line'), ('name', '=', 'sequence')], limit=1)
        self.assertEqual(
            wizard._map_field_value(line, '42', '%d-%m-%y', self.po_config), 42)

    def test_map_field_value_integer_invalid_defaults_zero(self):
        wizard = self.Wizard.create({})
        line = self.env['odoo.ocr.ai.config.line'].new({})
        line.ocr_field_id = self.IrModelFields.search(
            [('model', '=', 'purchase.order.line'), ('name', '=', 'sequence')], limit=1)
        self.assertEqual(
            wizard._map_field_value(line, 'not-a-number', '%d-%m-%y', self.po_config), 0)

    def test_map_field_value_float_strips_commas(self):
        wizard = self.Wizard.create({})
        line = self.env['odoo.ocr.ai.config.line'].new({})
        line.ocr_field_id = self.IrModelFields.search(
            [('model', '=', 'purchase.order.line'), ('name', '=', 'product_qty')], limit=1)
        self.assertEqual(
            wizard._map_field_value(line, '1,234.5', '%d-%m-%y', self.po_config), 1234.5)

    def test_map_field_value_monetary_strips_currency_symbol(self):
        wizard = self.Wizard.create({})
        line = self.env['odoo.ocr.ai.config.line'].new({})
        line.ocr_field_id = self.IrModelFields.search(
            [('model', '=', 'account.move'), ('name', '=', 'amount_total')], limit=1)
        self.assertEqual(
            wizard._map_field_value(line, '$1,050.00', '%d-%m-%y', self.po_config), 1050.0)

    def test_map_field_value_monetary_invalid_defaults_zero(self):
        wizard = self.Wizard.create({})
        line = self.env['odoo.ocr.ai.config.line'].new({})
        line.ocr_field_id = self.IrModelFields.search(
            [('model', '=', 'account.move'), ('name', '=', 'amount_total')], limit=1)
        self.assertEqual(
            wizard._map_field_value(line, 'n/a', '%d-%m-%y', self.po_config), 0.0)

    # ------------------------------------------------------------------
    # _resolve_many2one
    # ------------------------------------------------------------------

    def test_resolve_many2one_currency_found(self):
        wizard = self.Wizard.create({})
        line = self.env['odoo.ocr.ai.config.line'].new({})
        line.ocr_field_id = self.IrModelFields.search(
            [('model', '=', 'purchase.order'), ('name', '=', 'currency_id')], limit=1)
        usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        usd.active = True
        self.assertEqual(
            wizard._resolve_many2one(line, 'USD', self.po_config), usd.id)

    def test_resolve_many2one_currency_not_found_falls_back_to_company(self):
        wizard = self.Wizard.create({})
        line = self.env['odoo.ocr.ai.config.line'].new({})
        line.ocr_field_id = self.IrModelFields.search(
            [('model', '=', 'purchase.order'), ('name', '=', 'currency_id')], limit=1)
        self.assertEqual(
            wizard._resolve_many2one(line, 'NOT_A_REAL_CURRENCY', self.po_config),
            self.env.company.currency_id.id,
        )

    def test_resolve_many2one_partner_creates_when_not_found(self):
        wizard = self.Wizard.create({})
        line = self.ConfigLine.search(
            [('model_id', '=', self.po_config.id), ('title', '=', 'Vendor')], limit=1)
        value = {'name': 'OCR New Vendor', 'email': 'newvendor@example.com'}
        partner_id = wizard._resolve_many2one(line, value, self.po_config)
        partner = self.env['res.partner'].browse(partner_id)
        self.assertEqual(partner.name, 'OCR New Vendor')
        self.assertEqual(partner.email, 'newvendor@example.com')

    def test_resolve_many2one_partner_matches_by_email(self):
        existing = self.env['res.partner'].create({
            'name': 'Existing Vendor', 'email': 'existing@example.com',
        })
        wizard = self.Wizard.create({})
        line = self.ConfigLine.search(
            [('model_id', '=', self.po_config.id), ('title', '=', 'Vendor')], limit=1)
        value = {'name': 'Different Name On Doc', 'email': 'existing@example.com'}
        partner_id = wizard._resolve_many2one(line, value, self.po_config)
        self.assertEqual(partner_id, existing.id)

    def test_resolve_many2one_generic_relation_by_name(self):
        wizard = self.Wizard.create({})
        line = self.env['odoo.ocr.ai.config.line'].new({})
        line.ocr_field_id = self.IrModelFields.search(
            [('model', '=', 'purchase.order'), ('name', '=', 'fiscal_position_id')], limit=1)
        result = wizard._resolve_many2one(line, 'Nonexistent Fiscal Position', self.po_config)
        self.assertFalse(result)

    # ------------------------------------------------------------------
    # _resolve_many2many
    # ------------------------------------------------------------------

    def test_resolve_many2many_from_string_list(self):
        wizard = self.Wizard.create({})
        line = self.env['odoo.ocr.ai.config.line'].new({})
        line.ocr_field_id = self.IrModelFields.search(
            [('model', '=', 'res.partner'), ('name', '=', 'category_id')], limit=1)
        tag = self.env['res.partner.category'].create({'name': 'OCR Tag'})
        result = wizard._resolve_many2many(line, [tag.name])
        self.assertEqual(result, [(6, 0, [tag.id])])

    def test_resolve_many2many_empty_value_returns_false(self):
        wizard = self.Wizard.create({})
        line = self.env['odoo.ocr.ai.config.line'].new({})
        line.ocr_field_id = self.IrModelFields.search(
            [('model', '=', 'res.partner'), ('name', '=', 'category_id')], limit=1)
        self.assertFalse(wizard._resolve_many2many(line, False))

    # ------------------------------------------------------------------
    # _find_product / _resolve_taxes
    # ------------------------------------------------------------------

    def test_find_product_matches_by_default_code(self):
        product = self.env['product.product'].create({
            'name': 'Existing Widget',
            'default_code': 'WID-001',
            'publish_date': fields.Datetime.now(),
        })
        wizard = self.Wizard.create({})
        found = wizard._find_product('WID-001', 'Some Other Label', False)
        self.assertEqual(found, product)

    def test_find_product_creates_when_missing(self):
        wizard = self.Wizard.create({})
        found = wizard._find_product(None, 'Brand New OCR Product', True)
        self.assertTrue(found)
        self.assertEqual(found.name, 'Brand New OCR Product')

    def test_find_product_returns_empty_when_missing_and_not_allowed(self):
        wizard = self.Wizard.create({})
        found = wizard._find_product(None, 'Should Not Be Created', False)
        self.assertFalse(found)

    def test_resolve_taxes_by_percentage_string(self):
        tax = self.env['account.tax'].create({
            'name': 'OCR Test Tax 37.25%', 'amount': 37.25, 'amount_type': 'percent',
            'type_tax_use': 'purchase',
        })
        wizard = self.Wizard.create({})
        ids = wizard._resolve_taxes(['37.25%'], 'purchase.order.line')
        self.assertIn(tax.id, ids)

    def test_resolve_taxes_by_name(self):
        tax = self.env['account.tax'].create({
            'name': 'OCR Named Tax', 'amount': 5.0, 'amount_type': 'percent',
            'type_tax_use': 'purchase',
        })
        wizard = self.Wizard.create({})
        ids = wizard._resolve_taxes([{'name': 'OCR Named Tax'}], 'purchase.order.line')
        self.assertEqual(ids, [tax.id])

    # ------------------------------------------------------------------
    # action_create_record: end-to-end
    # ------------------------------------------------------------------

    def test_action_create_record_purchase_order(self):
        wizard = self._make_wizard({
            'status': True,
            'response': {
                'Vendor': {'name': 'ACME OCR Supplier', 'email': 'acme@ocrtest.com'},
                'Reference': 'PO-OCR-001',
                'Notes': 'Created automatically from scanned PO',
                'Order Lines': [
                    {'name': 'Steel Bracket', 'product_qty': '3', 'price_unit': '25.00'},
                ],
            },
        })
        action = wizard.action_create_record()
        self.assertEqual(action['res_model'], 'purchase.order')

        order = self.env['purchase.order'].browse(action['res_id'])
        self.assertTrue(order.is_created_ocr)
        self.assertEqual(order.ocr_attachment_id, wizard.ocr_attachment_id)
        self.assertEqual(order.partner_id.name, 'ACME OCR Supplier')
        self.assertEqual(order.partner_ref, 'PO-OCR-001')
        self.assertEqual(order.notes, 'Created automatically from scanned PO')
        self.assertEqual(len(order.order_line), 1)
        self.assertEqual(order.order_line.product_qty, 3)
        self.assertEqual(order.order_line.price_unit, 25.00)
        self.assertEqual(order.order_line.product_id.name, 'Steel Bracket')

    def test_action_create_record_posts_chatter_message(self):
        wizard = self._make_wizard({
            'status': True,
            'response': {
                'Vendor': {'name': 'Chatter Vendor', 'email': 'chatter@ocrtest.com'},
                'Reference': 'PO-OCR-002',
            },
        })
        action = wizard.action_create_record()
        order = self.env['purchase.order'].browse(action['res_id'])
        messages = order.message_ids.filtered(lambda m: 'Created via OCR' in (m.body or ''))
        self.assertTrue(messages)

    def test_action_create_record_raises_on_api_error_status(self):
        wizard = self._make_wizard({
            'status': False,
            'message': 'Document could not be read.',
        })
        with self.assertRaises(UserError):
            wizard.action_create_record()

    def test_action_create_record_raises_on_invalid_json(self):
        wizard = self._make_wizard({})
        wizard.response_text = 'not valid json {{'
        with self.assertRaises(UserError):
            wizard.action_create_record()

    # ------------------------------------------------------------------
    # action_send_to_ocr (network call mocked)
    # ------------------------------------------------------------------

    @patch('odoo.addons.ocr_ai_document.wizards.import_via_ocr.requests.post')
    def test_action_send_to_ocr_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'status': True,
            'response': {
                'request_usage': {
                    'Tokens Used': 10,
                    'Total Purchase Token': 1000,
                    'Total Used Token': 500,
                    'Total Available Token': 500,
                },
                'Vendor': {'name': 'Mocked Vendor'},
            },
        }
        mock_post.return_value = mock_response

        wizard = self.Wizard.create({
            'file_upload': PNG_B64,
            'file_upload_name': 'invoice.png',
        }).with_context(active_model='purchase.order')
        result = wizard.action_send_to_ocr()

        self.assertTrue(mock_post.called)
        self.assertTrue(wizard.ocr_response_received)
        self.assertEqual(wizard.used_token, 10)
        self.assertEqual(wizard.total_available_token, 500)
        self.assertTrue(wizard.ocr_attachment_id)
        self.assertEqual(result['res_model'], 'import.via.ocr')

    def test_action_send_to_ocr_requires_file(self):
        wizard = self.Wizard.create({})
        with self.assertRaises(UserError):
            wizard.action_send_to_ocr()

    def test_action_send_to_ocr_requires_active_config(self):
        self.po_config.active = False
        wizard = self.Wizard.create({
            'file_upload': PNG_B64,
            'file_upload_name': 'invoice.png',
        }).with_context(active_model='purchase.order')
        with self.assertRaises(UserError):
            wizard.action_send_to_ocr()

    @patch('odoo.addons.ocr_ai_document.wizards.import_via_ocr.requests.post')
    def test_action_send_to_ocr_rejects_oversized_file(self, mock_post):
        big_content = b'0' * (3 * 1024 * 1024)  # 3 MB, over the 2 MB limit
        wizard = self.Wizard.create({
            'file_upload': base64.b64encode(big_content),
            'file_upload_name': 'invoice.png',
        }).with_context(active_model='purchase.order')
        with self.assertRaises(UserError):
            wizard.action_send_to_ocr()
        mock_post.assert_not_called()


@tagged('post_install', '-at_install')
class TestOcrModelExtensions(TransactionCase):
    """Tests for the odoo.ocr.ai.mixin fields on account.move / purchase.order /
    sale.order / stock.picking, and their check_active_ocr_config helpers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.IrModel = cls.env['ir.model']
        cls.Config = cls.env['odoo.ocr.ai.config']

    def _enable_and_configure(self, model_name):
        model = self.IrModel.search([('model', '=', model_name)], limit=1)
        model.is_ocr_tus = True
        return self.Config.create({'model_id': model.id, 'active': True})

    def test_check_active_ocr_config_purchase_order_true(self):
        self._enable_and_configure('purchase.order')
        result = self.env['purchase.order'].check_active_ocr_config('purchase.order')
        self.assertTrue(result['active'])

    def test_check_active_ocr_config_purchase_order_false(self):
        result = self.env['purchase.order'].check_active_ocr_config('purchase.order')
        self.assertFalse(result['active'])

    def test_check_active_ocr_config_sale_order(self):
        self._enable_and_configure('sale.order')
        result = self.env['sale.order'].check_active_ocr_config('sale.order')
        self.assertTrue(result['active'])

    def test_check_active_ocr_config_stock_picking(self):
        self._enable_and_configure('stock.picking')
        result = self.env['stock.picking'].check_active_ocr_config('stock.picking')
        self.assertTrue(result['active'])

    def test_check_active_boolean_invoice(self):
        self._enable_and_configure('account.move')
        result = self.env['account.move'].check_active_boolean_invoice('account.move')
        self.assertTrue(result['active'])

    def test_create_links_attachment_res_id(self):
        """When a record is created with is_created_ocr + ocr_attachment_id,
        the attachment's res_id/res_model should be updated to point at it."""
        attachment = self.env['ir.attachment'].create({
            'name': 'linked.pdf',
            'mimetype': 'application/pdf',
            'datas': base64.b64encode(b'%PDF-1.4 fake'),
        })
        partner = self.env['res.partner'].create({'name': 'Link Test Vendor'})
        order = self.env['purchase.order'].create({
            'partner_id': partner.id,
            'is_created_ocr': True,
            'ocr_attachment_id': attachment.id,
        })
        self.assertEqual(attachment.res_id, order.id)
        self.assertEqual(attachment.res_model, 'purchase.order')

    def test_create_without_ocr_flag_does_not_touch_attachment(self):
        attachment = self.env['ir.attachment'].create({
            'name': 'untouched.pdf',
            'mimetype': 'application/pdf',
            'datas': base64.b64encode(b'%PDF-1.4 fake'),
        })
        partner = self.env['res.partner'].create({'name': 'Normal Vendor'})
        self.env['purchase.order'].create({'partner_id': partner.id})
        self.assertFalse(attachment.res_id)