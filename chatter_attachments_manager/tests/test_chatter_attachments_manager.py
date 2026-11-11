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
#############################################################################
import base64
import io
import zipfile
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError
from odoo.modules.module import get_manifest
from odoo.tests.common import HttpCase, TransactionCase, tagged

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import xlrd
except ImportError:
    xlrd = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None


@tagged("post_install", "-at_install")
class TestChatterAttachmentsManager(TransactionCase):
    """Test suite for Chatter Attachments Manager module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Chatter Partner",
                "email": "chatter_test@example.com",
            },
        )

        # 1x1 valid PNG image base64
        cls.dummy_png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00"
            b"\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        cls.dummy_png_base64 = base64.b64encode(
            cls.dummy_png_bytes,
        ).decode("ascii")

    def test_01_manifest_metadata_and_assets(self):
        """Verify manifest configuration, category, dependencies and assets."""
        manifest = get_manifest("chatter_attachments_manager")
        self.assertTrue(
            manifest,
            "Manifest for chatter_attachments_manager should be loadable.",
        )
        self.assertEqual(
            manifest.get("category"),
            "Discuss",
            "Category must be 'Discuss'.",
        )
        self.assertEqual(
            manifest.get("depends"),
            ["mail"],
            "Depends must contain only 'mail'.",
        )

        external_deps = manifest.get("external_dependencies", {}).get(
            "python",
            [],
        )
        self.assertIn(
            "qrcode",
            external_deps,
            "External python dependency 'qrcode' must be declared.",
        )

        assets = manifest.get("assets", {}).get("web.assets_backend", [])
        required_assets = [
            "chatter_attachments_manager/static/lib/fabric/fabric.min.js",
            "chatter_attachments_manager/static/lib/tui/tui-code-snippet.min.js",
            "chatter_attachments_manager/static/lib/tui/tui-color-picker.min.js",
            "chatter_attachments_manager/static/lib/filesaver/FileSaver.min.js",
            "chatter_attachments_manager/static/lib/tui/tui-image-editor.min.js",
            "chatter_attachments_manager/static/lib/tui/tui-image-editor.min.css",
            "chatter_attachments_manager/static/src/attachment_control_panel/attachment_control_panel.js",
            "chatter_attachments_manager/static/src/attachment_control_panel/attachment_control_panel_templates.xml",
            "chatter_attachments_manager/static/src/attachment_image/attachment_image.js",
            "chatter_attachments_manager/static/src/attachment_image/attachment_image_templates.xml",
            "chatter_attachments_manager/static/src/css/chatter_attachment_manager.css",
        ]
        for asset in required_assets:
            self.assertIn(
                asset,
                assets,
                f"Backend asset '{asset}' must be declared.",
            )

    def test_02_attachment_tag_model_and_constraints(self):
        """Test ir.attachment.tag creation, uniqueness and link to ir.attachment."""
        tag1 = self.env["ir.attachment.tag"].create(
            {
                "name": "Invoice",
                "color": 1,
            },
        )
        self.assertTrue(tag1.id, "Tag 1 should be created.")

        # Test tag without explicit color (covers _get_default_color)
        tag_default = self.env["ir.attachment.tag"].create(
            {
                "name": "Receipt",
            },
        )
        self.assertTrue(
            1 <= tag_default.color <= 11,
            "Default color must be between 1 and 11.",
        )

        with self.assertRaises(Exception), self.cr.savepoint():
            self.env["ir.attachment.tag"].create(
                {
                    "name": "Invoice",
                    "color": 2,
                },
            )

        attachment = self.env["ir.attachment"].create(
            {
                "name": "invoice_test.pdf",
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "tag_ids": [(6, 0, [tag1.id])],
            },
        )
        self.assertIn(
            tag1,
            attachment.tag_ids,
            "Tag should be linked to attachment.",
        )

    def test_03_decode_content_pdf_and_unsupported(self):
        """Test decode_content with PDF and unsupported files."""
        pdf_bytes = b"%PDF-1.4 sample pdf content %%EOF"
        attachment_pdf = self.env["ir.attachment"].create(
            {
                "name": "test.pdf",
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "mimetype": "application/pdf",
                "raw": pdf_bytes,
            },
        )
        pdf_res = self.env["ir.attachment"].decode_content(
            attachment_pdf.id,
            "pdf",
        )
        self.assertIsInstance(pdf_res, dict)
        self.assertEqual(pdf_res.get("type"), "pdf")
        self.assertTrue(pdf_res.get("data"))

        # Unsupported file
        attachment_txt = self.env["ir.attachment"].create(
            {
                "name": "test.unknown",
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "mimetype": "application/octet-stream",
                "raw": b"unsupported content",
            },
        )
        txt_res = self.env["ir.attachment"].decode_content(
            attachment_txt.id,
            "unknown",
        )
        self.assertEqual(txt_res, "Cannot preview this file.")

        # Empty attachment raw content
        attachment_empty = self.env["ir.attachment"].create(
            {
                "name": "empty.unknown",
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "raw": False,
            },
        )
        empty_res = self.env["ir.attachment"].decode_content(
            attachment_empty.id,
            "unknown",
        )
        self.assertEqual(empty_res, "Cannot preview this file.")

        # Non-existing attachment raises UserError
        with self.assertRaises(UserError):
            self.env["ir.attachment"].decode_content(99999999)

    def test_04_decode_content_docx_and_xlsx(self):
        """Test decode_content with DOCX, XLSX and XLS files."""
        # 1. DOCX decoding
        docx_attachment = self.env["ir.attachment"].create(
            {
                "name": "sample.docx",
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "mimetype": (
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
                "raw": b"sample docx data",
            },
        )

        # Uninstalled DocxDocument returns fallback message
        with patch(
            "odoo.addons.chatter_attachments_manager.models.ir_attachment.DocxDocument",
            None,
        ):
            uninstalled_res = self.env["ir.attachment"].decode_content(
                docx_attachment.id,
                "docx",
            )
            self.assertIn("No preview available", uninstalled_res)

        # Successful DocxDocument decoding
        class MockParagraph:
            def __init__(self, text):
                self.text = text

        class MockDoc:
            def __init__(self, *args, **kwargs):
                self.paragraphs = [
                    MockParagraph("Paragraph 1"),
                    MockParagraph("Paragraph 2"),
                ]

        with patch(
            "odoo.addons.chatter_attachments_manager.models.ir_attachment.DocxDocument",
            side_effect=MockDoc,
        ):
            docx_res = self.env["ir.attachment"].decode_content(
                docx_attachment.id,
                "docx",
            )
            self.assertIsInstance(docx_res, dict)
            self.assertEqual(docx_res.get("type"), "docx")
            self.assertEqual(
                docx_res.get("content"),
                ["Paragraph 1", "Paragraph 2"],
            )

            # Test doc_type=None inference from attachment.name
            inferred_res = self.env["ir.attachment"].decode_content(
                docx_attachment.id,
            )
            self.assertIsInstance(inferred_res, dict)
            self.assertEqual(inferred_res.get("type"), "docx")

        # Corrupted DOCX raises handled error
        with patch(
            "odoo.addons.chatter_attachments_manager.models.ir_attachment.DocxDocument",
            side_effect=ValueError("Corrupt docx"),
        ):
            corrupt_res = self.env["ir.attachment"].decode_content(
                docx_attachment.id,
                "docx",
            )
            self.assertIn("No preview available", corrupt_res)

        # 2. XLSX decoding with openpyxl
        if openpyxl is not None:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["Col1", "Col2"])
            ws.append(["Hello", 10])
            xlsx_buf = io.BytesIO()
            wb.save(xlsx_buf)

            xlsx_attachment = self.env["ir.attachment"].create(
                {
                    "name": "sample.xlsx",
                    "res_model": "res.partner",
                    "res_id": self.partner.id,
                    "mimetype": (
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                    "raw": xlsx_buf.getvalue(),
                },
            )
            xlsx_res = self.env["ir.attachment"].decode_content(
                xlsx_attachment.id,
                "xlsx",
            )
            self.assertIsInstance(xlsx_res, dict)
            self.assertEqual(xlsx_res.get("type"), "xlsx")
            self.assertIn("<th>Col1</th>", xlsx_res.get("content", ""))
            self.assertIn("<td>Hello</td>", xlsx_res.get("content", ""))

            # Test doc_type=None inference from attachment.name
            inferred_xlsx = self.env["ir.attachment"].decode_content(
                xlsx_attachment.id,
            )
            self.assertIsInstance(inferred_xlsx, dict)
            self.assertEqual(inferred_xlsx.get("type"), "xlsx")

            # Empty sheet (no rows)
            empty_wb = openpyxl.Workbook()
            empty_buf = io.BytesIO()
            empty_wb.save(empty_buf)
            empty_att = self.env["ir.attachment"].create(
                {
                    "name": "empty.xlsx",
                    "res_model": "res.partner",
                    "res_id": self.partner.id,
                    "raw": empty_buf.getvalue(),
                },
            )
            empty_res = self.env["ir.attachment"].decode_content(
                empty_att.id,
                "xlsx",
            )
            self.assertEqual(empty_res.get("type"), "xlsx")
            self.assertEqual(empty_res.get("content"), "<table></table>")

        # 3. XLS decoding with xlrd
        class MockSheet:
            def __init__(self):
                self.nrows = 2
                self.ncols = 2

            def cell_value(self, r, c):
                matrix = [["HeadA", "HeadB"], ["ValA", "ValB"]]
                return matrix[r][c]

        class MockBook:
            def sheet_by_index(self, index):
                return MockSheet()

        if xlrd is not None:
            with patch.object(xlrd, "open_workbook", return_value=MockBook()):
                xls_att = self.env["ir.attachment"].create(
                    {
                        "name": "sample.xls",
                        "res_model": "res.partner",
                        "res_id": self.partner.id,
                        "raw": b"dummy xls",
                    },
                )
                xls_res = self.env["ir.attachment"].decode_content(
                    xls_att.id,
                    "xls",
                )
                self.assertIsInstance(xls_res, dict)
                self.assertEqual(xls_res.get("type"), "xls")
                self.assertIn("<th>HeadA</th>", xls_res.get("content", ""))
                self.assertIn("<td>ValA</td>", xls_res.get("content", ""))

        # Corrupted xlsx preview returns fallback message
        corrupt_xlsx = self.env["ir.attachment"].create(
            {
                "name": "corrupt.xlsx",
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "raw": b"corrupted xlsx data",
            },
        )
        corrupt_xlsx_res = self.env["ir.attachment"].decode_content(
            corrupt_xlsx.id,
            "xlsx",
        )
        self.assertIn("No preview available", corrupt_xlsx_res)

        # Name without dot extension
        no_dot_att = self.env["ir.attachment"].create(
            {
                "name": "no_extension_file",
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "raw": b"some binary data",
            },
        )
        no_dot_res = self.env["ir.attachment"].decode_content(no_dot_att.id)
        self.assertEqual(no_dot_res, "Cannot preview this file.")

    def test_05_save_edited_image(self):
        """Test save_edited_image updates the attachment content properly."""
        attachment = self.env["ir.attachment"].create(
            {
                "name": "image_to_edit.png",
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "mimetype": "image/png",
                "raw": self.dummy_png_bytes,
            },
        )
        # With data: URI prefix and comma
        new_data_url = f"data:image/png;base64,{self.dummy_png_base64}"
        result = self.env["ir.attachment"].save_edited_image(
            attachment.id,
            new_data_url,
        )
        self.assertTrue(result)
        raw_val = (
            attachment.raw.content
            if hasattr(attachment.raw, "content")
            else bytes(attachment.raw)
        )
        self.assertEqual(
            raw_val,
            self.dummy_png_bytes,
        )

        # Raw base64 string without comma
        raw_res = self.env["ir.attachment"].save_edited_image(
            attachment.id,
            self.dummy_png_base64,
        )
        self.assertEqual(raw_res.get("id"), attachment.id)

        # Call with kwargs image
        kw_res = self.env["ir.attachment"].save_edited_image(
            attachment.id,
            image=self.dummy_png_base64,
        )
        self.assertEqual(kw_res.get("id"), attachment.id)

        # Call with empty image data
        empty_res = self.env["ir.attachment"].save_edited_image(
            attachment.id,
            None,
        )
        self.assertEqual(empty_res.get("id"), attachment.id)

        # Non-existing attachment raises UserError
        with self.assertRaises(UserError):
            self.env["ir.attachment"].save_edited_image(99999999)

    def test_06_generate_qr_code(self):
        """Test QR code generation for an attachment."""
        attachment = self.env["ir.attachment"].create(
            {
                "name": "qrcode_test.pdf",
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "raw": b"sample data",
            },
        )
        qr_data = self.env["ir.attachment"].generate_qr_code(attachment.id)
        self.assertIsInstance(
            qr_data,
            dict,
            "QR result should be a dictionary.",
        )
        if qr_data.get("image"):
            decoded = base64.b64decode(qr_data["image"])
            self.assertTrue(
                decoded.startswith(b"\x89PNG"),
                "QR code should be a valid PNG image.",
            )

        # Non-existing attachment raises UserError
        with self.assertRaises(UserError):
            self.env["ir.attachment"].generate_qr_code(99999999)

        # Test fallback when web.base.url is empty and token is generated
        with patch.object(
            type(self.env["ir.config_parameter"]),
            "get_str",
            return_value="",
        ):
            qr_fallback = self.env["ir.attachment"].generate_qr_code(attachment.id)
            self.assertTrue(qr_fallback.get("url"))

        # Token empty fallback (covers line 249)
        with patch.object(
            type(attachment), "access_token", new_callable=lambda: None,
        ), patch.object(
            type(attachment), "generate_access_token", return_value="",
        ):
            qr_no_token = self.env["ir.attachment"].generate_qr_code(attachment.id)
            self.assertIn("download=true", qr_no_token.get("url", ""))

        # Fallback when qrcode library is None
        with patch(
            "odoo.addons.chatter_attachments_manager.models.ir_attachment.qrcode",
            None,
        ):
            qr_none = self.env["ir.attachment"].generate_qr_code(attachment.id)
            self.assertEqual(qr_none, {})

    def test_07_access_rights_checks(self):
        """Ensure decode_content and save_edited_image enforce access checks."""
        with self.assertRaises(Exception):
            self.env["ir.attachment"].decode_content(99999999, "pdf")

        with self.assertRaises(Exception):
            self.env["ir.attachment"].save_edited_image(
                99999999,
                "data:image/png;base64,abc",
            )

        restricted_user = self.env["res.users"].create(
            {
                "name": "Restricted Attachment User",
                "login": "restricted_user_cam",
                "group_ids": [(6, 0, [self.env.ref("base.group_portal").id])],
            },
        )
        restricted_att = self.env["ir.attachment"].create(
            {
                "name": "secret_file.pdf",
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "public": False,
                "raw": b"%PDF-1.4 secret data %%EOF",
            },
        )
        try:
            restricted_att.with_user(restricted_user).check_access("read")
        except AccessError:
            with self.assertRaises(AccessError):
                self.env["ir.attachment"].with_user(
                    restricted_user,
                ).decode_content(restricted_att.id, "pdf")
            with self.assertRaises(AccessError):
                self.env["ir.attachment"].with_user(
                    restricted_user,
                ).save_edited_image(
                    restricted_att.id,
                    f"data:image/png;base64,{self.dummy_png_base64}",
                )

    def test_08_zip_download_logic(self):
        """Test creating and verifying zip archive containing attachments."""
        attachment1 = self.env["ir.attachment"].create(
            {
                "name": "file1.txt",
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "raw": b"Hello from file 1",
            },
        )
        attachment2 = self.env["ir.attachment"].create(
            {
                "name": "file2.txt",
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "raw": b"Hello from file 2",
            },
        )

        attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "res.partner"),
                ("res_id", "=", self.partner.id),
            ],
        )
        self.assertIn(attachment1, attachments)
        self.assertIn(attachment2, attachments)

        # Build in-memory zip archive mimicking controller download
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            for attach in attachments:
                if attach.raw:
                    data = (
                        attach.raw.content
                        if hasattr(attach.raw, "content")
                        else bytes(attach.raw)
                    )
                    archive.writestr(attach.name, data)

        stream.seek(0)
        with zipfile.ZipFile(stream, "r") as read_archive:
            namelist = read_archive.namelist()
            self.assertIn("file1.txt", namelist)
            self.assertIn("file2.txt", namelist)
            self.assertEqual(
                read_archive.read("file1.txt"),
                b"Hello from file 1",
            )
            self.assertEqual(
                read_archive.read("file2.txt"),
                b"Hello from file 2",
            )


@tagged("post_install", "-at_install")
class TestChatterAttachmentsManagerHttp(HttpCase):
    """HTTP test cases verifying controller routes and download endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_http_user = cls.env["res.users"].create(
            {
                "name": "HTTP Test User",
                "login": "cam_http_test_user",
                "password": "cam_http_test_password",
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
            },
        )
        cls.http_partner = cls.env["res.partner"].create(
            {
                "name": "Controller Partner Test",
            },
        )
        cls.att_a = cls.env["ir.attachment"].create(
            {
                "name": "doc_a.txt",
                "res_model": "res.partner",
                "res_id": cls.http_partner.id,
                "raw": b"Content of document A",
            },
        )
        cls.att_b = cls.env["ir.attachment"].create(
            {
                "name": "doc_b.txt",
                "res_model": "res.partner",
                "res_id": cls.http_partner.id,
                "raw": b"Content of document B",
            },
        )

    def test_09_download_document_controller_route(self):
        """Test the namespaced zip download controller endpoint."""
        self.authenticate("cam_http_test_user", "cam_http_test_password")

        url = f"/chatter_attachments_manager/download_document?param1=res.partner&param2={self.http_partner.id}"
        response = self.url_open(url)
        self.assertEqual(
            response.status_code,
            200,
            "Download endpoint should return HTTP 200.",
        )
        self.assertEqual(
            response.headers.get("Content-Type"),
            "application/zip",
            "Response Content-Type should be application/zip.",
        )

        zip_stream = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_stream, "r") as zf:
            files = zf.namelist()
            self.assertIn("doc_a.txt", files)
            self.assertIn("doc_b.txt", files)
            self.assertEqual(zf.read("doc_a.txt"), b"Content of document A")
            self.assertEqual(zf.read("doc_b.txt"), b"Content of document B")

    def test_10_download_document_controller_error_paths(self):
        """Test error handling in download controller with invalid inputs."""
        self.authenticate("cam_http_test_user", "cam_http_test_password")

        # Invalid model name with SQL/identifier characters
        res = self.url_open(
            "/chatter_attachments_manager/download_document?param1=invalid;;model&param2=1",
        )
        self.assertEqual(res.status_code, 404)

        # Model not in registry
        res = self.url_open(
            "/chatter_attachments_manager/download_document?param1=non.existent.model&param2=1",
        )
        self.assertEqual(res.status_code, 404)

        # Non-existent record id
        res = self.url_open(
            "/chatter_attachments_manager/download_document?param1=res.partner&param2=99999999",
        )
        self.assertEqual(res.status_code, 404)
