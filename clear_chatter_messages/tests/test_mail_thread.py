# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
################################################################################
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user

MANAGER_GROUP = "clear_chatter_messages.group_chatter_message_manager"


@tagged("post_install", "-at_install")
class TestClearChatterMessages(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.manager = new_test_user(
            cls.env,
            login="chatter_manager_test",
            groups="base.group_user,base.group_partner_manager,%s" % MANAGER_GROUP,
        )
        cls.normal_user = new_test_user(
            cls.env,
            login="chatter_normal_test",
            groups="base.group_user,base.group_partner_manager",
        )
        cls.partner = cls.env["res.partner"].with_context(
            mail_create_nolog=True
        ).create({"name": "Chatter Test Partner"})

    def test_access_denied(self):
        """Test unauthorized user access."""

        result = self.env["mail.thread"].with_user(
            self.normal_user
        ).action_clear_chatter_messages(
            "res.partner",
            self.partner.id,
        )

        self.assertFalse(result)

    def test_invalid_model(self):
        """Test empty model validation."""

        result = self.env["mail.thread"].with_user(
            self.manager
        ).action_clear_chatter_messages(
            "",
            self.partner.id,
        )

        self.assertFalse(result)

    def test_nonexistent_model(self):
        """Test nonexistent model validation."""

        result = self.env["mail.thread"].with_user(
            self.manager
        ).action_clear_chatter_messages(
            "invalid.model",
            self.partner.id,
        )

        self.assertFalse(result)

    def test_invalid_record_id(self):
        """Test invalid record IDs."""

        thread = self.env["mail.thread"].with_user(self.manager)

        for res_id in (0, -1, True, "invalid"):
            with self.subTest(res_id=res_id):
                result = thread.action_clear_chatter_messages(
                    "res.partner",
                    res_id,
                )
                self.assertFalse(result)

    def test_nonexistent_record(self):
        """Test nonexistent record validation."""

        result = self.env["mail.thread"].with_user(
            self.manager
        ).action_clear_chatter_messages(
            "res.partner",
            999999999,
        )

        self.assertFalse(result)

    def test_clear_chatter_messages(self):
        """Test successful chatter message deletion."""

        self.partner.message_post(
            body="Test chatter message"
        )

        messages = self.env["mail.message"].sudo().search([
            ("model", "=", "res.partner"),
            ("res_id", "=", self.partner.id),
        ])

        self.assertTrue(messages)

        result = self.env["mail.thread"].with_user(
            self.manager
        ).action_clear_chatter_messages(
            "res.partner",
            self.partner.id,
        )

        self.assertTrue(result)

        remaining_messages = self.env["mail.message"].sudo().search([
            ("model", "=", "res.partner"),
            ("res_id", "=", self.partner.id),
        ])

        self.assertFalse(remaining_messages)

    def test_clear_empty_chatter(self):
        """Test clearing a record without chatter messages."""

        result = self.env["mail.thread"].with_user(
            self.manager
        ).action_clear_chatter_messages(
            "res.partner",
            self.partner.id,
        )

        self.assertTrue(result)
