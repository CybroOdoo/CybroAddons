###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
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

import json
from types import SimpleNamespace
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.odoo_health_report.models import check_violations


@tagged('post_install', '-at_install')
class TestCheckViolations(TransactionCase):

    def setUp(self):
        super().setUp()
        self.module = 'odoo_health_report'
        self.module_path = '/tmp/odoo_health_report'

    def _completed(self, stdout='', stderr='', returncode=0):
        return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)

    def test_violations_report_maps_all_sections(self):
        violations = {
            'odoo_standards_check': ['standard'],
            'style_lint_check': ['style'],
            'code_quality_check': ['quality'],
            'mi_check': ['mi'],
            'import_sort_check': ['isort'],
            'code_format_check': ['black'],
            'cc_check': {'complexity': []},
            'security_scan': ['security'],
        }
        with patch.object(check_violations, 'get_violations', return_value=violations):
            report = check_violations.violations_report(self, self.module)
        self.assertEqual(report['module'], self.env.ref('base.module_odoo_health_report').display_name)
        self.assertEqual(report['violations']['style_lint'], ['style'])
        self.assertEqual(report['violations']['security_scan'], ['security'])

    def test_get_violations_calls_all_checkers(self):
        with (
            patch.object(check_violations, 'get_module_path', return_value=self.module_path),
            patch.object(check_violations, 'check_style_lint', return_value=['style']),
            patch.object(check_violations, 'check_code_quality', return_value=['quality']),
            patch.object(check_violations, 'check_maintainability_index', return_value=['mi']),
            patch.object(check_violations, 'check_import_sort', return_value=['isort']),
            patch.object(check_violations, 'check_code_format', return_value=['black']),
            patch.object(check_violations, 'check_code_complexity', return_value={'cc': []}),
            patch.object(check_violations, 'scan_code_security', return_value=['security']),
            patch.object(
                check_violations.check_odoo_python_guidelines,
                'check_odoo_python_standards',
                return_value=['standard'],
            ) as standards_mock,
        ):
            result = check_violations.get_violations(self.module)
        standards_mock.assert_called_once_with(name=self.module, path=self.module_path)
        self.assertEqual(result['style_lint_check'], ['style'])
        self.assertEqual(result['odoo_standards_check'], ['standard'])

    def test_style_lint_parses_flake8_output(self):
        stdout = f'{self.module_path}/models/demo.py:12:1: D100 Missing docstring\n'
        with (
            patch.object(check_violations, 'get_module_path', return_value=self.module_path),
            patch.object(check_violations.subprocess, 'run', return_value=self._completed(stdout=stdout)),
        ):
            result = check_violations.check_style_lint(self.module)
        self.assertEqual(result, [{
            'file_name': 'odoo_health_report/models/demo.py',
            'line_number': '12',
            'violation_message': ' D100 Missing docstring',
        }])

    def test_code_quality_parses_pylint_output(self):
        stdout = f'{self.module_path}/models/demo.py:10:4:odoolint: Message text\n'
        with (
            patch.object(check_violations, 'get_module_path', return_value=self.module_path),
            patch.object(check_violations.subprocess, 'run', return_value=self._completed(stdout=stdout)),
        ):
            result = check_violations.check_code_quality(self.module)
        self.assertEqual(result, [{
            'file': 'odoo_health_report/models/demo.py',
            'line': '10',
            'column': '4',
            'code': 'odoolint',
            'message': 'Message text',
        }])

    def test_maintainability_import_sort_format_complexity_and_security_parsers(self):
        with patch.object(check_violations, 'get_module_path', return_value=self.module_path):
            with patch.object(
                check_violations.subprocess,
                'run',
                return_value=self._completed(stdout=f'{self.module_path}/models/demo.py - A\n'),
            ):
                self.assertEqual(check_violations.check_maintainability_index(self.module), [{
                    'file': 'odoo_health_report/models/demo.py',
                    'grade': 'A',
                }])
            with patch.object(
                check_violations.subprocess,
                'run',
                return_value=self._completed(stderr=f'ERROR: {self.module_path}/models/demo.py Imports are incorrectly sorted.\n'),
            ):
                self.assertEqual(check_violations.check_import_sort(self.module), [{
                    'file': 'odoo_health_report/models/demo.py',
                    'message': 'Imports are incorrectly sorted.',
                }])
            with patch.object(
                check_violations.subprocess,
                'run',
                return_value=self._completed(stderr=f'would reformat {self.module_path}/models/demo.py\nAll done!\n'),
            ):
                self.assertEqual(
                    check_violations.check_code_format(self.module),
                    [('would reformat', f'{self.module_path}/models/demo.py')],
                )
            cc_output = json.dumps({
                f'{self.module_path}/models/demo.py': [{'name': 'demo'}],
                f'{self.module_path}/tests/test_demo.py': [{'name': 'ignored'}],
            })
            with patch.object(
                check_violations.subprocess,
                'run',
                return_value=self._completed(stdout=cc_output),
            ):
                self.assertEqual(check_violations.check_code_complexity(self.module), {
                    f'{self.module_path}/models/demo.py': [{'name': 'demo'}],
                })
            security_output = json.dumps({'results': [{'filename': 'demo.py'}]})
            with patch.object(
                check_violations.subprocess,
                'run',
                return_value=self._completed(stdout=security_output),
            ):
                self.assertEqual(check_violations.scan_code_security(self.module), [{
                    'filename': 'demo.py',
                }])

    def test_black_output_helpers_identify_file_lines(self):
        self.assertEqual(
            check_violations.parse_black_output_simple('would reformat demo.py'),
            ('would reformat', 'demo.py'),
        )
        self.assertEqual(check_violations.parse_black_output_simple('unchanged'), (None, None))
        self.assertTrue(check_violations.is_file_line('reformatted demo.py'))
        self.assertFalse(check_violations.is_file_line('All done!'))
