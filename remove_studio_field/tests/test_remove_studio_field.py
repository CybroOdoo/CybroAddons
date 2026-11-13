# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRemoveStudioField(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.enterClassContext(cls.registry_test_mode())
        cls.partner_model = cls.env["ir.model"]._get("res.partner")

    def _create_studio_field(self, name):
        return self.env["ir.model.fields"].create({
            "name": name,
            "model_id": self.partner_model.id,
            "ttype": "char",
            "field_description": f"Test Studio Field {name}",
            "state": "manual",
        })

    def _create_wizard(self, fields):
        return self.env["remove.studio.field"].create({
            "field_ids": [Command.set(fields.ids)],
        })

    def test_action_removes_unreferenced_studio_field(self):
        field = self._create_studio_field("x_studio_remove_test_field")
        wizard = self._create_wizard(field)

        result = wizard.action_remove_studio_field()

        self.assertFalse(field.exists())
        self.assertEqual(result["tag"], "display_notification")
        self.assertEqual(result["params"]["type"], "success")

    def test_action_rejects_field_used_in_a_view(self):
        field = self._create_studio_field("x_studio_view_test_field")
        view = self.env["ir.ui.view"].create({
            "name": "test.remove.studio.field.view",
            "model": "res.partner",
            "type": "form",
            "arch_db": (
                "<form><sheet><group><field name='x_studio_view_test_field'/>"
                "</group></sheet></form>"
            ),
        })
        wizard = self._create_wizard(field)

        with self.assertRaisesRegex(UserError, "Cannot delete the fields"):
            wizard.action_remove_studio_field()

        self.assertTrue(field.exists())
        self.assertTrue(view.exists())

    def test_action_checks_all_selected_fields_before_deleting(self):
        unused_field = self._create_studio_field("x_studio_unused_test_field")
        used_field = self._create_studio_field("x_studio_used_test_field")
        self.env["ir.ui.view"].create({
            "name": "test.remove.studio.field.multiple.view",
            "model": "res.partner",
            "type": "form",
            "arch_db": (
                "<form><sheet><group><field name='x_studio_used_test_field'/>"
                "</group></sheet></form>"
            ),
        })
        wizard = self._create_wizard(unused_field | used_field)

        with self.assertRaises(UserError):
            wizard.action_remove_studio_field()

        self.assertTrue(unused_field.exists())
        self.assertTrue(used_field.exists())
