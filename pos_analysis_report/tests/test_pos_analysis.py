# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged("post_install", "-at_install")
class TestPosAnalysis(TestPoSCommon):
    """Tests for the POS analysis wizard."""

    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.session = self.open_new_session()

    def test_action_print_pdf_raises_for_invalid_date_range(self):
        wizard = self.env["pos.analysis"].create({
            "from_date": fields.Date.to_date("2026-01-31"),
            "to_date": fields.Date.to_date("2026-01-01"),
        })

        with self.assertRaises(ValidationError):
            wizard.action_print_pdf()

    def test_action_print_pdf_returns_report_action_with_filters(self):
        wizard = self.env["pos.analysis"].create({
            "from_date": fields.Date.to_date("2026-01-01"),
            "to_date": fields.Date.to_date("2026-01-31"),
            "pos_session_id": self.session.id,
            "partner_id": self.customer.id,
        })

        action = wizard.with_context(discard_logo_check=True).action_print_pdf()

        self.assertEqual(action["type"], "ir.actions.report")
        self.assertEqual(
            action["report_name"],
            "pos_analysis_report.report_pos_analysis",
        )
        self.assertEqual(action["data"], {
            "from_date": fields.Date.to_date("2026-01-01"),
            "to_date": fields.Date.to_date("2026-01-31"),
            "pos_session_id": self.session.id,
            "partner_id": self.customer.id,
        })
