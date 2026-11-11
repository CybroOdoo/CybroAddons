# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from unittest.mock import patch
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPurchaseFormatEditor(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.layout = cls.env['doc.layout.purchase'].create({
            'name': 'Test Layout',
            'base_color': '#000000',
        })
        cls.company = cls.env.company
        cls.company.write({
            'base_layout_purchase': 'default',
            'document_layout_purchase_id': cls.layout.id,
        })
        cls.partner = cls.env["res.partner"].create({
            "name": "Test Purchase Vendor",
            "email": "vendor@test.com",
        })
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
        })
        cls.report_layout = cls.env["report.layout"].search([], limit=1)
        if not cls.report_layout:
            cls.report_layout = cls.env["report.layout"].create(
                {
                    "name": "Test Report Layout",
                    "view_id": cls.env.ref("web.external_layout_standard").id,
                }
            )

    def test_related_fields(self):
        """Test related fields in purchase order."""
        self.assertEqual(
            self.purchase_order.theme_id_purchase,
            self.layout
        )
        self.assertEqual(
            self.purchase_order.company_id.base_layout_purchase,
            'default'
        )

    def test_print_pdf_action(self):
        """Test PDF preview action."""
        wizard = self.env['base.document.layout'].create({
            'company_id': self.company.id,
        })
        action = wizard.print_pdf()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertIn('/purchase/pdf/preview', action['url'])

    def test_compute_preview_default_layout(self):
        """Test preview generation for default purchase layout."""
        self.company.base_layout_purchase = "default"
        wizard = self.env["base.document.layout"].create({
            "company_id": self.company.id,
            "report_layout_id": self.report_layout.id,
        })
        view_model = self.env["ir.ui.view"]
        with patch.object(
            type(view_model), "_render_template", return_value="<div>Preview</div>"
        ) as mock_render:
            wizard._compute_preview()
            mock_render.assert_called_once()
            self.assertIn("report_preview_default_purchase", str(mock_render.call_args))

    def test_compute_preview_normal_layout(self):
        """Test preview generation for normal purchase layout."""
        self.company.base_layout_purchase = "normal"
        wizard = self.env["base.document.layout"].create({
            "company_id": self.company.id,
            "report_layout_id": self.report_layout.id,
        })
        view_model = self.env["ir.ui.view"]
        with patch.object(
            type(view_model), "_render_template", return_value="<div>Preview</div>"
        ) as mock_render:
            wizard._compute_preview()
            mock_render.assert_called_once()
            self.assertIn("report_preview_normal_purchase", str(mock_render.call_args))

    def test_compute_preview_modern_layout(self):
        """Test preview generation for modern purchase layout."""
        self.company.base_layout_purchase = "modern"
        wizard = self.env["base.document.layout"].create({
            "company_id": self.company.id,
            "report_layout_id": self.report_layout.id,
        })
        view_model = self.env["ir.ui.view"]
        with patch.object(
            type(view_model), "_render_template", return_value="<div>Preview</div>"
        ) as mock_render:
            wizard._compute_preview()
            mock_render.assert_called_once()
            self.assertIn("report_preview_modern_purchase", str(mock_render.call_args))

    def test_compute_preview_old_layout(self):
        """Test preview generation for old purchase layout."""
        self.company.base_layout_purchase = "old"
        wizard = self.env["base.document.layout"].create({
            "company_id": self.company.id,
            "report_layout_id": self.report_layout.id,
        })
        view_model = self.env["ir.ui.view"]
        with patch.object(
            type(view_model), "_render_template", return_value="<div>Preview</div>"
        ) as mock_render:
            wizard._compute_preview()
            mock_render.assert_called_once()
            self.assertIn("report_preview_old_purchase", str(mock_render.call_args))

    def test_compute_preview_without_report_layout(self):
        """Test preview computation without a report layout."""
        wizard = self.env["base.document.layout"].create({
            "company_id": self.company.id,
            "report_layout_id": False,
        })
        view_model = self.env["ir.ui.view"]
        with patch.object(type(view_model), "_render_template") as mock_render:
            wizard._compute_preview()
            mock_render.assert_not_called()
