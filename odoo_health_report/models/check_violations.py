# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import re
import subprocess

import sys

from odoo.modules import get_module_path
from . import check_odoo_python_guidelines


def violations_report(self, module):
    """
    Check the violations for selected modules for PDF report.

    Args:
        self (obj): The odoo ClassDef.
        module (str): The module technical name.

    Returns:
        dict: Module name and its violations
    """
    violations = get_violations(module)
    report_dict = {
        'module': self.env.ref(f'base.module_{module}').display_name,
        'violations': {
            "odoo_standards": violations.get('odoo_standards_check'),
            "style_lint": violations.get('style_lint_check'),
            "code_quality": violations.get('code_quality_check'),
            "maintainability_index": violations.get('mi_check'),
            "import_sort": violations.get('import_sort_check'),
            "code_format": violations.get('code_format_check'),
            "code_complexity": violations.get('cc_check'),
            "security_scan": violations.get('security_scan')
        }
    }
    return report_dict

def get_violations(module):
    """
    Check the violations for selected module.

    Args:
        module (str): The module technical name.

    Returns:
        dict: Selected module violations
    """
    return {
        "style_lint_check": check_style_lint(module),
        "code_quality_check": check_code_quality(module),
        "mi_check": check_maintainability_index(module),
        "import_sort_check": check_import_sort(module),
        "code_format_check": check_code_format(module),
        "cc_check": check_code_complexity(module),
        "security_scan": scan_code_security(module),
        "odoo_standards_check": check_odoo_python_guidelines.check_odoo_python_standards(
            name=module, path=get_module_path(module))
    }

def check_style_lint(module):
    """
    Check the style and lint for selected module .

    Args:
        module (str): The module technical name.

    Returns:
        list of dictionaries for the violations with the file name and line number.
    """
    excluded_files = ['__init__.py', '__manifest__.py', '__pycache__', '*.pyc', '.git', 'tests']
    ignored_violations = ['E501', 'E301', 'E302']

    venv_python = sys.executable
    exclude_param = f"--exclude={','.join(excluded_files)}"
    ignore_param = f"--ignore={','.join(ignored_violations)}"
    module_path = get_module_path(module)

    result = subprocess.run(
        [venv_python, '-m', 'flake8', '--select=D', exclude_param, ignore_param, module_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    violations = result.stdout.strip().splitlines()

    violations_list = []
    for violation in violations:
        parts = violation.split(":", 3)
        if len(parts) >= 4:
            file_path = f"{module}/{parts[0].split(f'/{module}/')[1]}"
            violations_list.append({
                'file_name': file_path,
                'line_number': parts[1],
                'violation_message': parts[3]
            })
    return violations_list

def check_code_quality(module):
    """
    Check the code quality for selected module .

    Args:
        module (str): The module technical name.

    Returns:
        list of dictionaries for the violations with the file name, code, line and column number.
    """
    pylint_result = subprocess.run([
        sys.executable, '-m', 'pylint',
        '--load-plugins=pylint_odoo',
        '-d all',
        '-e odoolint',
        '--ignore=tests',
        '--ignore-patterns=__init__.py,__manifest__.py',
        get_module_path(module)
    ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    output = pylint_result.stdout.strip().splitlines()
    result = []
    for rec in output:
        if rec.startswith(('*', '-')) or rec == '':
            continue
        else:
            rec = rec.split(':')
            if len(rec) >= 5:
                file_path = f"{module}/{rec[0].split(f'/{module}/')[1]}"
                result.append({
                    'file': file_path,
                    'line': rec[1],
                    'column': rec[2],
                    'code': rec[3].strip(),
                    'message': rec[4].strip(),
                })
    return result

def check_maintainability_index(module):
    """
        Check the maintainability index for selected module .

        Args:
            module (str): The module technical name.

        Returns:
            list of dictionaries for the file name and grade.
    """
    result = subprocess.run([
        sys.executable, '-m', 'radon',
        'mi',
        get_module_path(module),
    ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    excluded_files = ("__init__.py", "__manifest__.py")
    mi_list = []
    for rec in result.stdout.splitlines():
        if not any(exclude in rec for exclude in excluded_files):
            rec = rec.split(' - ')
            if len(rec) >= 2:
                file_path = f"{module}/{rec[0].split(f'/{module}/')[1]}"
                if file_path.startswith(f'{module}/tests/'):
                    continue
                mi_list.append({'file': file_path, 'grade': rec[1]})
    return mi_list

def check_import_sort(module):
    """
        Check the import sorting for selected module .

        Args:
            module (str): The module technical name.

        Returns:
            list of dictionaries for the file name and message.
    """
    result = subprocess.run([
        sys.executable, '-m', 'isort',
        '--check-only',
        '--skip', '__init__.py',
        '--skip', '__manifest__.py',
        '--skip', 'tests',
        get_module_path(module),
    ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    import_sort_list = []
    for rec in result.stderr.splitlines():
        rec = rec.replace("ERROR: ", "")
        parts = rec.split(" ", 1)
        if len(parts) >= 2:
            file_path = f"{module}/{parts[0].split(f'/{module}/')[1]}"
            import_sort_list.append({'file': file_path, 'message': parts[1]})
    return import_sort_list

def parse_black_output_simple(line):
    """Simple parsing for all Black output types"""
    actions = ['would reformat ', 'reformatted ', 'formatted ', 'would format ']
    for action in actions:
        if line.startswith(action):
            filename = line[len(action):]
            return action.strip(), filename
    return None, None

def is_file_line(line):
    """Check if line is a file entry (not summary)"""
    skip_patterns = ['💥', '💔', '!', 'files would be', 'file would be', 'All done']
    actions = ['would reformat ', 'reformatted ', 'formatted ', 'would format ']
    if any(pattern in line for pattern in skip_patterns):
        return False
    return any(line.startswith(action) for action in actions)

def check_code_format(module):
    """
        Check the code format for selected module .

        Args:
            module (str): The module technical name.

        Returns:
            list of dictionaries for the file name and action.
    """
    result = subprocess.run([
        sys.executable, '-m', 'black',
        '--check',
        '--exclude', '__init__.py|__manifest__.py|tests',
        get_module_path(module),
    ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    code_format_list = []
    for line in result.stderr.strip().split('\n'):
        line = line.strip()
        if not line or not is_file_line(line):
            continue
        parsed = parse_black_output_simple(line)
        if parsed[0] is not None:
            code_format_list.append(parsed)

    return code_format_list

def check_code_complexity(module):
    """
        Check the code complexity for selected module .

        Args:
            module (str): The module technical name.

        Returns:
            list of dictionaries for the file name and grade.
    """
    result = subprocess.run([
        sys.executable, '-m', 'radon',
        'cc',
        '--json',
        get_module_path(module),
    ],
        capture_output=True,
        text=True
    )

    if result.returncode == 0 and result.stdout:
        clean_stdout = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
        cc_dict = json.loads(clean_stdout.strip())
        cc_dict = {
            k: v for k, v in cc_dict.items()
            if '/tests/' not in k
        }

        return cc_dict
    return {}

def scan_code_security(module):
    """
        Scan the code security for selected module .

        Args:
            module (str): The module technical name.

        Returns:
            list of dictionaries of the security scan.
    """
    result = subprocess.run([
        sys.executable, '-m', 'bandit',
        '-r', get_module_path(module),
        '-x', '__init__.py,__manifest__.py,tests',
        '-f', 'json', '--quiet'
    ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True)

    if result.stdout:
        security_list = json.loads(result.stdout).get('results', [])
        return security_list
    return []
