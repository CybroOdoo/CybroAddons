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
import json
from types import SimpleNamespace
from unittest.mock import patch

from odoo.modules import get_module_path
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.odoo_health_report.models import check_violations

MODULE = 'odoo_health_report'


def _fake_run(args, **kwargs):
    """Return canned tool output so the parsers can be tested without the tools."""
    path = get_module_path(MODULE)
    target = f'{path}/models/sample.py'
    tool = next((a for a in args if a in ('flake8', 'pylint', 'radon', 'isort', 'black', 'bandit')), '')
    if tool == 'flake8':
        return SimpleNamespace(returncode=1, stdout=f'{target}:3:1: D100 Missing docstring', stderr='')
    if tool == 'pylint':
        return SimpleNamespace(
            returncode=0, stderr='',
            stdout=f'************* Module x\n{target}:4:0: C8101: Missing author\n')
    if tool == 'radon' and 'cc' in args:
        payload = {target: [{'name': 'f', 'complexity': 3}], f'{path}/tests/t.py': []}
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr='')
    if tool == 'radon':
        return SimpleNamespace(returncode=0, stderr='', stdout=f'{target} - A\n{path}/tests/t.py - A\n')
    if tool == 'isort':
        return SimpleNamespace(returncode=1, stdout='', stderr=f'ERROR: {target} Imports are incorrectly sorted')
    if tool == 'black':
        return SimpleNamespace(returncode=1, stdout='', stderr=f'would reformat {target}\nAll done! 1 file would be reformatted.')
    if tool == 'bandit':
        return SimpleNamespace(returncode=1, stderr='', stdout=json.dumps({'results': [{'issue_text': 'x'}]}))
    return SimpleNamespace(returncode=1, stdout='', stderr='')


@tagged('post_install', '-at_install')
class TestViolations(TransactionCase):
    """Tests for the external tool wrappers (tool output is mocked)."""

    def _run(self, function):
        with patch.object(check_violations.subprocess, 'run', side_effect=_fake_run):
            return function(MODULE)

    def test_style_lint(self):
        result = self._run(check_violations.check_style_lint)
        self.assertEqual(result[0]['line_number'], '3')
        self.assertEqual(result[0]['file_name'], f'{MODULE}/models/sample.py')

    def test_code_quality(self):
        result = self._run(check_violations.check_code_quality)
        self.assertEqual(result[0]['line'], '4')
        self.assertEqual(result[0]['file'], f'{MODULE}/models/sample.py')

    def test_maintainability_index(self):
        result = self._run(check_violations.check_maintainability_index)
        self.assertEqual(result, [{'file': f'{MODULE}/models/sample.py', 'grade': 'A'}])

    def test_import_sort(self):
        result = self._run(check_violations.check_import_sort)
        self.assertEqual(len(result), 1)
        self.assertIn('incorrectly sorted', result[0]['message'])

    def test_code_format(self):
        result = self._run(check_violations.check_code_format)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'would reformat')

    def test_code_complexity(self):
        result = self._run(check_violations.check_code_complexity)
        self.assertEqual(len(result), 1)
        self.assertTrue(all('/tests/' not in key for key in result))

    def test_security_scan(self):
        self.assertEqual(self._run(check_violations.scan_code_security), [{'issue_text': 'x'}])

    def test_empty_tool_output(self):
        empty = SimpleNamespace(returncode=1, stdout='', stderr='')
        with patch.object(check_violations.subprocess, 'run', return_value=empty):
            self.assertEqual(check_violations.check_code_complexity(MODULE), {})
            self.assertEqual(check_violations.scan_code_security(MODULE), [])
            self.assertEqual(check_violations.check_code_format(MODULE), [])

    def test_black_helpers(self):
        self.assertEqual(check_violations.parse_black_output_simple('would reformat a.py'),
                         ('would reformat', 'a.py'))
        self.assertEqual(check_violations.parse_black_output_simple('nothing'), (None, None))
        self.assertTrue(check_violations.is_file_line('would reformat a.py'))
        self.assertFalse(check_violations.is_file_line('All done!'))

    def test_get_violations_and_report(self):
        with patch.object(check_violations.subprocess, 'run', side_effect=_fake_run):
            data = check_violations.get_violations(MODULE)
            report = check_violations.violations_report(self.env['module.quality.package'], MODULE)
        self.assertEqual(len(data), 8)
        self.assertEqual(set(report['violations']), {
            'odoo_standards', 'style_lint', 'code_quality', 'maintainability_index',
            'import_sort', 'code_format', 'code_complexity', 'security_scan'})
