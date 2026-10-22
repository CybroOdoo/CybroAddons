# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import json

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import VibeCommon


@tagged("post_install", "-at_install")
class TestGeneratedModule(VibeCommon):

    def setUp(self):
        super().setUp()
        self.conv = self._make_conversation()
        self.module = self._make_module(self.conv)

    def test_technical_name_constraint(self):
        for bad in ("Library", "1library"):
            with self.subTest(name=bad), self.assertRaises(ValidationError):
                self.module.technical_name = bad

    def test_refinement_flag(self):
        self.assertFalse(self.module.is_refinement)
        child = self._make_module(self.conv, parent_module_id=self.module.id,
                                  revision_number=2)
        self.assertTrue(child.is_refinement)
        self.assertEqual(self.module.child_module_ids, child)

    def test_download_url(self):
        self.assertEqual(self.module.action_download(),
                         "/vibe/module/%d/download" % self.module.id)

    def test_validation_errors_list(self):
        self.assertEqual(self.module.get_validation_errors_list(), [])
        errors = [{"file": "a.py", "line": 2, "message": "m"}]
        self.module.validation_errors = json.dumps(errors)
        self.assertEqual(self.module.get_validation_errors_list(), errors)
        self.module.validation_errors = "{not json"
        self.assertEqual(self.module.get_validation_errors_list(), [])


@tagged("post_install", "-at_install")
class TestGeneratedFile(VibeCommon):

    def setUp(self):
        super().setUp()
        self.conv = self._make_conversation()
        self.module = self._make_module(self.conv)
        self.file = self.module.file_ids.filtered(
            lambda f: f.path == "__manifest__.py")

    def test_language_compute(self):
        mapping = {"a.py": "python", "x.unknown": "plaintext"}
        for path, language in mapping.items():
            with self.subTest(path=path):
                rec = self.env["vibe.generated.file"].create({
                    "module_id": self.module.id, "path": path, "content": "x"})
                self.assertEqual(rec.language, language)

    def test_unique_path_per_module(self):
        with mute_logger("odoo.sql_db"), self.assertRaises(Exception), \
                self.env.cr.savepoint():
            self.env["vibe.generated.file"].create({
                "module_id": self.module.id, "path": "__init__.py",
                "content": "x"})

    def test_save_content(self):
        with self.assertRaises(UserError):
            self.file.save_content(None)
        result = self.file.save_content("{'name': 'Changed'}\n")
        self.assertTrue(result["user_modified"])
        self.assertEqual(result["content"], "{'name': 'Changed'}\n")
        self.assertIn(result["validation_state"], ("valid", "invalid"))
        self.assertEqual(self.module.validation_state, result["validation_state"])

    def test_save_content_with_broken_manifest_data(self):
        self.module.manifest_data = "{broken"
        result = self.file.save_content("x")
        self.assertEqual(result["validation_state"], "invalid")
