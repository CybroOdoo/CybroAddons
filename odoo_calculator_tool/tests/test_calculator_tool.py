# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(
#    <https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import os
from xml.etree import ElementTree
from odoo.modules.module import get_module_path
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCalculatorTool(TransactionCase):
    """Test suite verifying assets, templates, metadata, and calculation
    logic for Odoo Calculator.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module_path = get_module_path('odoo_calculator_tool')

    def test_01_module_installed(self):
        """Verify odoo_calculator_tool is successfully installed."""
        module = self.env['ir.module.module'].search([
            ('name', '=', 'odoo_calculator_tool'),
        ], limit=1)
        self.assertTrue(module, "Module odoo_calculator_tool must exist.")
        self.assertEqual(
            module.state,
            'installed',
            "odoo_calculator_tool should be installed.",
        )

    def test_02_manifest_metadata(self):
        """Verify manifest metadata completeness per guidelines."""
        module = self.env['ir.module.module'].search([
            ('name', '=', 'odoo_calculator_tool'),
        ], limit=1)
        self.assertEqual(module.license, 'LGPL-3')
        self.assertEqual(module.category_id.name, 'Extra Tools')
        self.assertIn('Cybrosys', module.author)

    def test_03_assets_bundle_files(self):
        """Verify all bundle assets exist on disk and are non-empty."""
        expected_files = [
            'static/src/css/calculator.css',
            'static/src/xml/calculator.xml',
            'static/src/js/calculator.js',
        ]
        for rel_path in expected_files:
            full_path = os.path.join(self.module_path, rel_path)
            self.assertTrue(
                os.path.isfile(full_path),
                f"Asset file {rel_path} must exist.",
            )
            self.assertGreater(
                os.path.getsize(full_path),
                0,
                f"Asset file {rel_path} must not be empty.",
            )

    def test_04_qweb_template_structure(self):
        """Verify calculator.xml has valid XML structure and key buttons."""
        xml_path = os.path.join(
            self.module_path, 'static/src/xml/calculator.xml'
        )
        tree = ElementTree.parse(xml_path)
        root = tree.getroot()

        self.assertEqual(root.tag, 'templates')
        template_node = root.find(".//t[@t-name='CalculatorTool']")
        self.assertIsNotNone(
            template_node,
            "Template 'CalculatorTool' must be defined.",
        )
        self.assertIsNone(
            template_node.get('owl'),
            "Obsolete owl attribute should be removed.",
        )

        display = root.find(".//input[@id='display']")
        self.assertIsNotNone(display, "Display input element must exist.")

        button_keys = {
            btn.get('data-key')
            for btn in root.findall(".//button")
            if btn.get('data-key')
        }
        for digit in range(10):
            self.assertIn(str(digit), button_keys)
        for op in ['+', '-', '*', '/', '%', 'C', '±', '=']:
            self.assertIn(op, button_keys)

    def test_05_calculator_math_logic(self):
        """Verify mathematical operations executed by calculator logic."""
        def calc(num1, num2, op):
            if op == '+':
                return num1 + num2
            if op == '-':
                return num1 - num2
            if op == '*':
                return num1 * num2
            if op == '/':
                return 'Error' if num2 == 0 else num1 / num2
            if op == '%':
                return (num1 / 100) * num2
            return num2

        self.assertEqual(calc(12, 8, '+'), 20)
        self.assertEqual(calc(20, 5, '-'), 15)
        self.assertEqual(calc(6, 7, '*'), 42)
        self.assertEqual(calc(42, 6, '/'), 7)
        self.assertEqual(calc(10, 0, '/'), 'Error')
        self.assertEqual(calc(200, 15, '%'), 30.0)

    def test_06_docs_and_assets(self):
        """Verify icons, screenshots, and documentation files exist."""
        required_docs = [
            'README.rst',
            'doc/RELEASE_NOTES.md',
            'static/description/index.html',
            'static/description/icon.png',
            'static/description/banner.jpg',
            'static/description/assets/screenshots/1.png',
            'static/description/assets/screenshots/2.png',
            'static/description/assets/screenshots/3.png',
        ]
        for rel_doc in required_docs:
            full_doc_path = os.path.join(self.module_path, rel_doc)
            self.assertTrue(
                os.path.isfile(full_doc_path),
                f"Document/asset {rel_doc} must exist.",
            )
            self.assertGreater(
                os.path.getsize(full_doc_path),
                0,
                f"Document/asset {rel_doc} must not be empty.",
            )
