# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
######################################################################################

import ast
import os
import shutil
import tempfile
from odoo.tests import TransactionCase, tagged
from odoo.addons.odoo_health_report.models import check_odoo_python_guidelines as guidelines


@tagged('post_install', '-at_install')
class TestCheckOdooPythonGuidelines(TransactionCase):
    """Test suite for checking Odoo Python guidelines and standards."""

    def setUp(self):
        """Set up the test environment by initializing guidelines and a temporary module path."""
        super().setUp()
        guidelines.results.clear()
        guidelines.module_technical_name[0] = 'sample_module'
        self.tmpdir = tempfile.mkdtemp()
        self.module_path = os.path.join(self.tmpdir, 'sample_module')
        os.makedirs(self.module_path)

    def tearDown(self):
        """Tear down the test environment and clean up temporary directories."""
        shutil.rmtree(self.tmpdir)
        guidelines.results.clear()
        guidelines.module_technical_name[0] = 'no_module'
        super().tearDown()

    def _write(self, relative_path, content):
        """Helper method to create a file within the temporary module path."""
        path = os.path.join(self.module_path, relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
        return path

    def test_case_helpers_validate_expected_patterns(self):
        """Test if camel case and snake case validators work as expected."""
        self.assertTrue(guidelines.is_camel_case('ValidClass1'))
        self.assertFalse(guidelines.is_camel_case('invalid_class'))
        self.assertTrue(guidelines.is_snake_case('valid_name_1'))
        self.assertFalse(guidelines.is_snake_case('InvalidName'))

    def test_class_function_field_and_variable_checks_collect_violations(self):
        """Test if class, function, field, and variable checks collect correct violations."""
        file_path = self._write('models/bad_model.py', """
from odoo import api, fields, models

class bad_model(models.Model):
    _name = 'bad.models'
    partner = fields.Many2one('res.partner')
    tag = fields.Many2many('res.partner.category')
    value = fields.Char(compute='_compute_wrong')

    @api.depends('value')
    def compute_value(self):
        Partner = self.env['res.partner']
        partner = Partner.browse(1)
        records = Partner.search([])
        BadName = Partner.search([])
        return partner, records, BadName
""")
        guidelines.analyze_file(file_path)
        issues = [result['issue'] for result in guidelines.results]
        self.assertIn("Class name 'bad_model' is not CamelCase", issues)
        self.assertIn("Many2one field 'partner' should end with '_id'", issues)
        self.assertIn("Many2many field 'tag' should end with '_ids'", issues)
        self.assertIn("Method 'compute_value' uses @depends but doesn't start with '_compute_'", issues)
        self.assertIn("Compute method should be named '_compute_value' for field 'value', found '_compute_wrong'", issues)
        self.assertIn("Variable 'partner' may represent a single record, use _id suffix", issues)
        self.assertIn("Variable 'records' may represent multiple records, use _ids suffix", issues)
        self.assertIn("Variable name 'BadName' is not snake_case", issues)

    def test_direct_ast_checks_collect_missing_docstring_and_bad_method_names(self):
        """Test AST based checks for missing docstrings and incorrect method names."""
        file_path = self._write('models/actions.py', """
class GoodClass:
    def BadMethod(self):
        pass

    def do_confirm(self):
        pass
""")
        tree = ast.parse(open(file_path, encoding='utf-8').read())
        class_node = tree.body[0]
        bad_method = class_node.body[0]
        action_method = class_node.body[1]
        guidelines.check_missing_docstring(class_node, file_path, type='class')
        guidelines.check_function_name(bad_method, file_path)
        guidelines.check_method_prefix(action_method, file_path)
        issues = [result['issue'] for result in guidelines.results]
        self.assertIn("Class 'GoodClass' is missing a docstring", issues)
        self.assertIn("Function name 'BadMethod' is not snake_case", issues)
        self.assertIn("Action method 'do_confirm' should start with 'action_'", issues)

    def test_manifest_and_location_checks_collect_expected_violations(self):
        """Test if manifest validations and model location checks correctly identify violations."""
        manifest_path = self._write('__manifest__.py', """
{
    'name': 'Sample',
    'version': '1.0',
    'depends': ['base', ''],
    'data': ['views/view.xml', 'security/ir.model.access.csv'],
    'license': 'BAD',
}
""")
        transient_path = self._write('models/sample_wizard.py', """
from odoo import models

class SampleWizard(models.TransientModel):
    _name = 'sample.wizard'
""")
        report_path = self._write('models/sample_report.py', """
from odoo import models

class SampleReport(models.AbstractModel):
    _name = 'report.sample_module.sample_report'
""")
        controller_path = self._write('controllers/main.py', """
from odoo import http

class SampleController(http.Controller):
    pass
""")
        guidelines.check_manifest_file(manifest_path)
        guidelines.check_transient_model_location(transient_path)
        guidelines.check_report_model_location(report_path)
        guidelines.check_controller_naming(self.module_path + os.sep, 'sample_module')
        issues = [result['issue'] for result in guidelines.results]
        self.assertIn("Version '1.0' does not follow '18.0.1.0.0' format", issues)
        self.assertIn("Empty string in 'depends'", issues)
        self.assertIn("License 'BAD' is not a recognized Odoo-compatible license", issues)
        self.assertIn("'security' file 'security/ir.model.access.csv' appears after non-security files", issues)
        self.assertIn("TransientModel class 'SampleWizard' is not in a 'wizard/' directory", issues)
        self.assertIn("Report model 'report.sample_module.sample_report' is not in a 'report/' directory", issues)
        self.assertIn("'main.py' is deprecated for controller files", issues)
        self.assertTrue(controller_path)

    def test_scan_directory_skips_test_files_and_returns_results(self):
        """Test if the directory scanner properly skips test files and processes actual source files."""
        self._write('models/test_skipped.py', "class BadName:\n    pass\n")
        self._write('models/real_file.py', "class bad_name:\n    pass\n")
        result = guidelines.check_odoo_python_standards('sample_module', self.module_path)
        files = {item['file'] for item in result}
        self.assertNotIn('sample_module/models/test_skipped.py', files)
        self.assertIn('sample_module/models/real_file.py', files)
