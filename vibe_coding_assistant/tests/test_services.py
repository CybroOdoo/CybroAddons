# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: FATHIMA SHALFA P (odoo@cybrosys.com)
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
###############################################################################
"""Unit tests for the pure-Python service layer (no network, no ORM writes)."""
import json

from odoo.tests import TransactionCase, tagged

from ..services.module_validator import validate
from ..services.response_parser import ResponseParseError, parse
from ..services.template_merger import _substitute, merge_templates

VALID_MANIFEST = """{
    'name': 'Product Brand',
    'version': '18.0.1.0.0',
    'depends': ['product'],
    'license': 'LGPL-3',
    'data': ['security/ir.model.access.csv'],
}"""


def _envelope(**overrides):
    """Return a minimal, valid generation envelope."""
    files = {
        "__manifest__.py": VALID_MANIFEST,
        "__init__.py": "from . import models\n",
        "models/__init__.py": "from . import product_brand\n",
        "models/product_brand.py": (
            "from odoo import fields, models\n\n\n"
            "class ProductBrand(models.Model):\n"
            "    _name = 'product.brand'\n"
            "    name = fields.Char()\n"
        ),
        "security/ir.model.access.csv": "id,name,model_id:id\n",
    }
    files.update(overrides.pop("files", {}))
    module = {
        "technical_name": "product_brand",
        "display_name": "Product Brand",
        "version": "18.0.1.0.0",
        "depends": ["product"],
    }
    module.update(overrides)
    return {
        "module": module,
        "files": [
            {"path": p, "content": c} for p, c in files.items() if c is not None
        ],
    }


@tagged("post_install", "-at_install")
class TestResponseParser(TransactionCase):

    def test_parse_plain_json(self):
        data = parse(json.dumps(_envelope()))
        self.assertEqual(data["module"]["technical_name"], "product_brand")

    def test_parse_strips_fences_and_prose(self):
        raw = "Sure! Here it is:\n```json\n%s\n```\nEnjoy." % json.dumps(_envelope())
        self.assertIn("files", parse(raw))

    def test_parse_no_json(self):
        with self.assertRaises(ResponseParseError):
            parse("I cannot help with that.")

    def test_parse_invalid_json(self):
        with self.assertRaises(ResponseParseError):
            parse("{module: nope}")

    def test_parse_ai_reported_error(self):
        with self.assertRaisesRegex(ResponseParseError, "out of scope"):
            parse('{"error": "out of scope"}')

    def test_parse_bad_shape(self):
        with self.assertRaises(ResponseParseError):
            parse('{"module": [], "files": []}')
        with self.assertRaises(ResponseParseError):
            parse('{"module": {}, "files": {}}')
        with self.assertRaises(ResponseParseError):
            parse('{"module": {}, "files": [{"path": "a.py"}]}')


@tagged("post_install", "-at_install")
class TestModuleValidator(TransactionCase):

    def _messages(self, parsed):
        return " | ".join(e["message"] for e in validate(parsed))

    def test_valid_module(self):
        self.assertEqual(validate(_envelope()), [])

    def test_bad_technical_name_and_version(self):
        msgs = self._messages(_envelope(technical_name="Bad-Name", version="1.0"))
        self.assertIn("Invalid technical_name", msgs)
        self.assertIn("Invalid version", msgs)

    def test_missing_required_files(self):
        msgs = self._messages(_envelope(files={"__init__.py": None}))
        self.assertIn("Required file missing: __init__.py", msgs)

    def test_manifest_problems(self):
        msgs = self._messages(_envelope(files={"__manifest__.py": "{'name': 'x', 'depends': 'base'}"}))
        self.assertIn("missing required key: 'version'", msgs)
        self.assertIn("'depends' must be a list", msgs)
        msgs = self._messages(_envelope(files={"__manifest__.py": "{'name': "}))
        self.assertIn("Manifest parse error", msgs)

    def test_manifest_data_reference_missing(self):
        manifest = VALID_MANIFEST.replace(
            "'security/ir.model.access.csv'", "'views/missing.xml'")
        msgs = self._messages(_envelope(files={"__manifest__.py": manifest}))
        self.assertIn("references missing file: 'views/missing.xml'", msgs)

    def test_models_init_and_security(self):
        msgs = self._messages(_envelope(files={
            "models/__init__.py": "",
            "security/ir.model.access.csv": None,
            "__manifest__.py": VALID_MANIFEST.replace(
                "'data': ['security/ir.model.access.csv'],", ""),
        }))
        self.assertIn("does not appear to import 'product_brand'", msgs)
        self.assertIn("ir.model.access.csv is missing", msgs)

    def test_python_and_xml_syntax(self):
        errors = validate(_envelope(files={
            "models/broken.py": "def oops(:\n",
            "models/__init__.py": "from . import product_brand, broken\n",
            "views/view.xml": "<odoo><record></odoo>",
        }))
        files = {e["file"] for e in errors}
        self.assertIn("models/broken.py", files)
        self.assertIn("views/view.xml", files)


@tagged("post_install", "-at_install")
class TestTemplateMerger(TransactionCase):

    def test_substitute(self):
        self.assertEqual(
            _substitute("{{ technical_name }} / {{unknown}}", {"technical_name": "abc"}),
            "abc / {{unknown}}",
        )

    def test_merge_adds_templates_with_variables(self):
        parsed = merge_templates(_envelope())
        paths = {f["path"] for f in parsed["files"]}
        self.assertIn("README.md", paths)
        self.assertIn("doc/RELEASE_NOTES.md", paths)
        for f in parsed["files"]:
            if f["path"] in ("README.md", "doc/RELEASE_NOTES.md",
                             "static/description/index.html"):
                self.assertNotIn("{{technical_name}}", f["content"])
                self.assertNotIn("{{ technical_name }}", f["content"])

    def test_merge_never_overwrites_ai_files(self):
        parsed = merge_templates(_envelope(files={"README.md": "AI README"}))
        readmes = [f for f in parsed["files"] if f["path"] == "README.md"]
        self.assertEqual(len(readmes), 1)
        self.assertEqual(readmes[0]["content"], "AI README")
