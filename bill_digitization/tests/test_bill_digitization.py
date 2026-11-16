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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import io
from datetime import date
from unittest.mock import patch

import pytesseract
from pdf2image.exceptions import PDFSyntaxError
from PIL import Image, ImageDraw, ImageFont

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestBillDigitization(AccountTestInvoicingCommon):
    """Test suite for Bill Digitization settings, OCR wizard, and parsers."""

    OCR_PATCH = (
        'odoo.addons.bill_digitization.wizard.digitize_bill.'
        'pytesseract.image_to_string'
    )
    PDF_CONVERT_PATCH = (
        'odoo.addons.bill_digitization.wizard.digitize_bill.convert_from_bytes'
    )

    @classmethod
    def setUpClass(cls):
        """Set up shared wizard reference and synthetic OCR sample fixtures."""
        super().setUpClass()
        cls.wizard_model = cls.env['digitize.bill']

    def _render_bill_image(self, text_body, mode='RGBA'):
        """Render a crisp synthetic bill image for end-to-end OCR tests."""
        img = Image.new(mode, (1200, 500), color='white')
        drawer = ImageDraw.Draw(img)
        font = ImageFont.load_default(size=32)
        fill_color = 0 if mode == 'L' else 'black'
        drawer.text((40, 40), text_body, fill=fill_color, font=font)
        return img

    def _encode_image_b64(self, img, img_format='PNG'):
        """Encode a PIL image to a base64 string accepted by Odoo Binary."""
        buffer = io.BytesIO()
        img.save(buffer, format=img_format)
        return base64.b64encode(buffer.getvalue()).decode()

    def test_01_settings_and_access_control(self):
        """Verify settings persistence, helper RPC, and invoicing ACL rules."""
        self.assertFalse(self.wizard_model.is_digitize_bill_enabled())

        settings = self.env['res.config.settings'].create({'digitize_bill': True})
        settings.execute()
        self.assertTrue(self.wizard_model.is_digitize_bill_enabled())

        invoice_user = self.env['res.users'].create({
            'name': 'Bill User',
            'login': 'bill_digitization_invoice_user',
            'email': 'bill.user@example.com',
            'group_ids': [(6, 0, [self.env.ref('account.group_account_invoice').id])],
        })
        self.assertTrue(
            self.wizard_model.with_user(invoice_user).is_digitize_bill_enabled(),
        )
        sample_b64 = self._encode_image_b64(self._render_bill_image("Sample Bill"))
        user_wiz = self.wizard_model.with_user(invoice_user).create({
            'bill': sample_b64,
            'file_name': 'sample.png',
        })
        self.assertTrue(user_wiz.exists())

        portal_user = self.env['res.users'].create({
            'name': 'Plain Portal User',
            'login': 'bill_digitization_portal_user',
            'email': 'portal.user@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        with self.assertRaises(AccessError):
            self.wizard_model.with_user(portal_user).create({
                'bill': sample_b64,
                'file_name': 'denied.png',
            })

        settings_off = self.env['res.config.settings'].create({'digitize_bill': False})
        settings_off.execute()
        self.assertFalse(self.wizard_model.is_digitize_bill_enabled())

    def test_02_clean_number_and_product_name(self):
        """Verify OCR number normalization and product name sanitization."""
        wiz = self.wizard_model
        self.assertEqual(wiz.clean_number(None), 0.0)
        self.assertEqual(wiz.clean_number('abc'), 0.0)
        self.assertEqual(wiz.clean_number('ab1'), 0.0)
        self.assertEqual(wiz.clean_number('12@3'), 0.0)
        self.assertEqual(wiz.clean_number('$1,250.50'), 1250.5)
        self.assertEqual(wiz.clean_number('1OO'), 0.0)
        self.assertEqual(wiz.clean_number('10O'), 100.0)
        self.assertEqual(wiz.clean_number('l2'), 12.0)
        self.assertEqual(wiz.clean_number('I5'), 15.0)
        self.assertEqual(wiz.clean_number('19-95'), 19.95)
        self.assertEqual(wiz.clean_number('12.34.56'), 12.3456)
        self.assertEqual(wiz.clean_number('1000000000'), 0.0)
        self.assertEqual(wiz.clean_number('1..5'), 1.5)
        self.assertEqual(wiz.clean_number('(25)'), 250.0)
        self.assertEqual(wiz.clean_number('...1'), 1.0)
        self.assertEqual(wiz.clean_number('---'), 0.0)
        self.assertEqual(wiz.clean_number('-1-2'), 1.0)
        with patch.object(type(wiz), '_try_parse_bounded_float', side_effect=[None, 42.0]):
            self.assertEqual(wiz.clean_number('42.0'), 42.0)

        cleaned = wiz.clean_product_name("Title\rNew\n [SKU-1] USB_Cable|Pro (2m) - ")
        self.assertEqual(cleaned, "USB Cable Pro")

    def test_03_address_and_product_line_validation(self):
        """Verify address heuristics and non-product line filtering."""
        wiz = self.wizard_model
        self.assertTrue(wiz.is_likely_address("Main, NY, USA"))
        self.assertTrue(wiz.is_likely_address("First Ave, Block 12345, Downtown"))
        self.assertTrue(wiz.is_likely_address("first part, second part, third part"))
        self.assertFalse(wiz.is_likely_address("Office Chair, Ergonomic Back, Leather"))
        self.assertTrue(wiz.is_likely_address("742 Evergreen Street"))
        self.assertTrue(wiz.is_likely_address("PO Box 9981"))

        self.assertFalse(wiz.is_valid_product_line("ab"))
        self.assertFalse(wiz.is_valid_product_line("Invoice Total"))
        self.assertFalse(wiz.is_valid_product_line("Ship To Warehouse"))
        self.assertFalse(wiz.is_valid_product_line("120 Oak Avenue"))
        self.assertFalse(wiz.is_valid_product_line("item item item chair"))
        self.assertFalse(wiz.is_valid_product_line("--- +++ *** 12"))
        self.assertFalse(wiz.is_valid_product_line("A" * 101))
        self.assertTrue(wiz.is_valid_product_line("Wireless Keyboard"))

    def test_04_normalize_line_data_and_intelligent_parser(self):
        """Verify tuple normalization, fallback parser, and OCR cleanup."""
        wiz = self.wizard_model
        normalized = wiz.normalize_line_data([
            ('Short',),
            ('10', '20'),
            ('Invoice Header', '2', '50.00'),
            ('Desk Pad', '2', '15.00', '30.00'),
            ('Swapped Widget', '15.00', '2', '30.00'),
            ('Decimal Heuristic', '19.99', '3'),
            ('Expensive Item', '99999', '10.00'),
            ('Single Price Item', '45.00'),
            ('Too Large Qty', '10001', '150'),
        ])
        self.assertEqual(len(normalized), 5)
        self.assertEqual(normalized[0], ('Desk Pad', '2.0', '15.0'))
        self.assertEqual(normalized[1], ('Swapped Widget', '15.0', '2.0'))
        self.assertEqual(normalized[2], ('Decimal Heuristic', '3.0', '19.99'))
        self.assertEqual(normalized[3], ('Expensive Item', '10.0', '99999.0'))
        self.assertEqual(normalized[4], ('Single Price Item', '1.0', '45.0'))

        parsed = wiz.parse_lines_intelligently(
            "x\n"
            "1 | \n"
            "OnlyOneWord\n"
            "1 | Ergonomic Mouse 3 25.00 75.00\n"
            "Laptop Stand 45.00 2\n"
            "Total 100.00 1\n"
            "SingleNumberItem 50.00",
        )
        self.assertEqual(
            parsed,
            [
                ('Ergonomic Mouse', '3.0', '25.0'),
                ('Laptop Stand', '2.0', '45.0'),
            ],
        )

        cleaned_ocr = wiz.clean_ocr_text("1.i $O.50 1O2 l2 I5 5l ")
        self.assertIn("1.1", cleaned_ocr)
        self.assertIn("$0.50", cleaned_ocr)
        self.assertIn("102", cleaned_ocr)
        self.assertIn("12", cleaned_ocr)
        self.assertIn("15", cleaned_ocr)
        self.assertIn("51", cleaned_ocr)

    def test_05_create_record_formats_and_line_commands(self):
        """Verify bill creation across regex layouts and line builders."""
        wiz = self.wizard_model

        bill1 = wiz.create_record(
            "Bill No: BILL-101\nDate: 15/09/2026\n"
            "[SKU01] Widget Alpha Units 2 50.00 100.00",
        )
        self.assertEqual(bill1.move_type, 'in_invoice')
        self.assertEqual(bill1.ref, 'BILL-101')
        self.assertEqual(bill1.invoice_date, date(2026, 9, 15))
        self.assertEqual(len(bill1.invoice_line_ids), 1)
        self.assertEqual(bill1.invoice_line_ids.product_id.name, 'Widget Alpha')
        self.assertEqual(bill1.invoice_line_ids.quantity, 2.0)
        self.assertEqual(bill1.invoice_line_ids.price_unit, 50.0)
        self.assertFalse(bill1.invoice_line_ids.tax_ids)

        bill1_repeat = wiz.create_record(
            "Bill No: BILL-102\nDate: 99/99/2026\n"
            "[SKU01] Widget Alpha Units 1 50.00 50.00",
        )
        self.assertEqual(
            bill1_repeat.invoice_line_ids.product_id,
            bill1.invoice_line_ids.product_id,
        )
        self.assertEqual(bill1_repeat.invoice_date, fields.Date.context_today(wiz))

        bill2 = wiz.create_record("10 Paper Ream Each 5 8.00 40.00")
        self.assertEqual(bill2.invoice_line_ids.product_id.name, 'Paper Ream')
        self.assertEqual(bill2.invoice_line_ids.quantity, 5.0)

        bill3 = wiz.create_record("Monitor Mount $49.50 2 $99.00")
        self.assertEqual(bill3.invoice_line_ids.product_id.name, 'Monitor Mount')
        self.assertEqual(bill3.invoice_line_ids.price_unit, 49.5)

        bill4 = wiz.create_record("Header\nStanding Desk 2 250.00 500.00")
        self.assertTrue(bill4.invoice_line_ids)

        bill5 = wiz.create_record("[VB1] Desk Mat 3.0 20.0 0.0% $ 60.0")
        self.assertEqual(bill5.invoice_line_ids.quantity, 3.0)
        self.assertEqual(bill5.invoice_line_ids.price_unit, 20.0)

        bill6 = wiz.create_record("Header\nEthernet Cable $15.00 3 $45.00")
        self.assertTrue(bill6.invoice_line_ids)

        bill_price_qty = wiz.create_record("Header\nUSB Hub 25.00 2 50.00")
        self.assertEqual(bill_price_qty.invoice_line_ids.product_id.name, 'USB Hub')
        self.assertEqual(bill_price_qty.invoice_line_ids.price_unit, 25.0)
        self.assertEqual(bill_price_qty.invoice_line_ids.quantity, 2.0)

        bill7 = wiz.create_record("Header\nCloud Backup 120.00")
        self.assertTrue(bill7.invoice_line_ids)

        bill8 = wiz.create_record(
            "Description\n[R01] Enterprise Router\n\n"
            "Quantity Unit Price Taxes\n2.00 75.00 0.00% $ 150.00\n\n",
        )
        self.assertEqual(bill8.invoice_line_ids.product_id.name, 'Enterprise Router')
        self.assertEqual(bill8.invoice_line_ids.quantity, 2.0)
        self.assertEqual(bill8.invoice_line_ids.price_unit, 75.0)

        bill9 = wiz.create_record("Thank you for your business")
        self.assertFalse(bill9.invoice_line_ids)

        product = bill1.invoice_line_ids.product_id
        cmds_price = wiz._build_move_line_commands([product], [], [30.0], [30.0])
        self.assertEqual(cmds_price[0][2]['quantity'], 1.0)
        self.assertEqual(cmds_price[0][2]['price_unit'], 30.0)

        cmds_sub = wiz._build_move_line_commands([product], [2.0], [], [80.0])
        self.assertEqual(cmds_sub[0][2]['quantity'], 2.0)
        self.assertEqual(cmds_sub[0][2]['price_unit'], 40.0)

        sample_matches = wiz._extract_text_patterns("Thank you for your business")
        sample_matches['double_line_name'] = [
            ('Cable', 'Tray', 'Unit', '2', '$15.00', '30.00'),
        ]
        line_cmds = wiz.record_lines(sample_matches)
        self.assertEqual(len(line_cmds), 1)
        self.assertEqual(line_cmds[0][2]['quantity'], 2.0)
        self.assertEqual(line_cmds[0][2]['price_unit'], 15.0)

    def test_06_action_add_document_real_image_and_pdf(self):
        """Verify PNG and PDF digitization flow using mocked OCR/PDF tools."""
        bill_text = (
            "Bill No: INV-2026-001\n"
            "Date: 11/11/2026\n"
            "[SKU10] Office Chair 2 150.00 300.00\n"
        )
        png_img = self._render_bill_image(bill_text, mode='RGBA')
        png_wiz = self.wizard_model.create({
            'bill': self._encode_image_b64(png_img, 'PNG'),
            'file_name': 'vendor_bill.png',
        })
        pdf_img = self._render_bill_image(bill_text, mode='RGB')
        pdf_wiz = self.wizard_model.create({
            'bill': self._encode_image_b64(pdf_img, 'PDF'),
            'file_name': 'vendor_bill.pdf',
        })

        def _fake_ocr(processed_img, **_kwargs):
            """Validate preprocessed image and return fixture text."""
            self.assertEqual(processed_img.mode, 'L')
            self.assertGreaterEqual(processed_img.width, 2000)
            return bill_text

        with (
            patch(self.OCR_PATCH, side_effect=_fake_ocr) as mock_ocr,
            patch(self.PDF_CONVERT_PATCH, return_value=[pdf_img]) as mock_pdf,
        ):
            action = png_wiz.action_add_document()
            self.assertEqual(action['res_model'], 'account.move')
            self.assertEqual(action['view_mode'], 'form')
            self.assertEqual(action['target'], 'current')

            move = self.env['account.move'].browse(action['res_id'])
            self.assertEqual(move.move_type, 'in_invoice')
            self.assertEqual(move.state, 'draft')
            self.assertEqual(move.ref, 'INV-2026-001')
            self.assertEqual(move.invoice_date, date(2026, 11, 11))
            self.assertTrue(move.invoice_line_ids)

            moved_att = self.env['ir.attachment'].search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', move.id),
            ])
            self.assertTrue(moved_att)

            pdf_action = pdf_wiz.action_add_document()
            pdf_move = self.env['account.move'].browse(pdf_action['res_id'])
            self.assertEqual(pdf_move.move_type, 'in_invoice')
            self.assertTrue(pdf_move.invoice_line_ids)
            mock_pdf.assert_called_once()
            self.assertEqual(mock_pdf.call_args.kwargs.get('dpi'), 400)
            self.assertEqual(mock_ocr.call_count, 2)

    def test_07_action_add_document_error_paths(self):
        """Verify ValidationError handling on invalid files and OCR errors."""
        empty_wiz = self.wizard_model.create({'file_name': 'empty.png'})
        with self.assertRaises(ValidationError):
            empty_wiz.action_add_document()

        invalid_img_wiz = self.wizard_model.create({
            'bill': base64.b64encode(b'not-an-image').decode(),
            'file_name': 'corrupt.png',
        })
        with self.assertRaises(ValidationError):
            invalid_img_wiz.action_add_document()

        invalid_pdf_wiz = self.wizard_model.create({
            'bill': base64.b64encode(b'not-a-pdf').decode(),
            'file_name': 'corrupt.pdf',
        })
        with (
            patch(self.PDF_CONVERT_PATCH, side_effect=PDFSyntaxError('corrupt pdf')),
            self.assertRaises(ValidationError),
        ):
            invalid_pdf_wiz.action_add_document()

        valid_png_wiz = self.wizard_model.create({
            'bill': self._encode_image_b64(self._render_bill_image("Sample Bill")),
            'file_name': 'valid.png',
        })

        for patch_kwargs in (
            {'side_effect': pytesseract.TesseractNotFoundError()},
            {'side_effect': pytesseract.TesseractError(1, 'ocr failure')},
            {'return_value': 'ok'},
        ):
            with (
                patch(self.OCR_PATCH, **patch_kwargs),
                self.assertRaises(ValidationError),
            ):
                valid_png_wiz.action_add_document()

        pdf_page = self._render_bill_image("Sample PDF", mode='RGB')
        valid_pdf_wiz = self.wizard_model.create({
            'bill': self._encode_image_b64(pdf_page, 'PDF'),
            'file_name': 'sample.pdf',
        })
        with (
            patch(self.PDF_CONVERT_PATCH, return_value=[]),
            self.assertRaises(ValidationError),
        ):
            valid_pdf_wiz.action_add_document()

        with (
            patch(self.PDF_CONVERT_PATCH, return_value=[pdf_page]),
            patch(self.OCR_PATCH, return_value=''),
            self.assertRaises(ValidationError),
        ):
            valid_pdf_wiz.action_add_document()
