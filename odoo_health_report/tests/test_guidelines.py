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
import os
import shutil
import tempfile

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.odoo_health_report.models import check_odoo_python_guidelines as guidelines

BAD_MODEL = """
from odoo import fields, models


class wrongName(models.Model):
    _name = 'Wrong_Names'
    nameField = fields.Char()
    partner = fields.Many2one('res.partner')
    partners = fields.Many2many('res.partner')
    lines = fields.One2many('res.partner', 'id')
    total = fields.Float(compute='_compute_other')

    def BadMethod(self):
        Partner = self.env['res.partner']
        record = Partner.search([])
        single = Partner.browse(1)
        someVar = 1
        return record, single, someVar

    @api.onchange('partner')
    def wrong_onchange(self):
        pass

    @api.constrains('partner')
    def wrong_constrain(self):
        pass

    @api.depends('partner')
    def wrong_compute(self):
        pass


class Plain(models.Model):
    pass


class Helper(models.TransientModel):
    _name = 'helper.wizard'


class ReportHelper(models.AbstractModel):
    _name = 'report.fixture.mod'
"""

GOOD_MODEL = """
from odoo import fields, models


class GoodModel(models.Model):
    \"\"\"Documented model.\"\"\"
    _name = 'good.model'

    name = fields.Char()
    total = fields.Float(compute='_compute_total')

    def _compute_total(self):
        \"\"\"Documented method.\"\"\"
        for rec in self:
            rec.total = 1.0
"""

BAD_MANIFEST = "{'name': 'Fixture', 'version': '1.0', 'depends': ['base']}"


@tagged('post_install', '-at_install')
class TestGuidelines(TransactionCase):
    """Tests for the Odoo Python guideline checker."""

    def setUp(self):
        super().setUp()
        self.base_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.base_dir, True)
        self.path = os.path.join(self.base_dir, 'fixture_mod')
        for sub in ('models', 'controllers', 'wizard'):
            os.makedirs(os.path.join(self.path, sub))
        self._write('__manifest__.py', BAD_MANIFEST)
        self._write('models/BadFile.py', BAD_MODEL)
        self._write('models/good_model.py', GOOD_MODEL)
        self._write('models/broken.py', 'def broken(:\n')
        self._write('controllers/other.py', 'from odoo import http\n\n\nclass Other(http.Controller):\n    pass\n')

    def _write(self, relative, content):
        with open(os.path.join(self.path, relative), 'w', encoding='utf-8') as handle:
            handle.write(content)

    def test_case_helpers(self):
        self.assertTrue(guidelines.is_camel_case('GoodName'))
        self.assertFalse(guidelines.is_camel_case('bad_name'))
        self.assertTrue(guidelines.is_snake_case('good_name'))
        self.assertFalse(guidelines.is_snake_case('BadName'))

    def test_fixture_module_reports_violations(self):
        results = guidelines.check_odoo_python_standards('fixture_mod', self.path)
        self.assertTrue(results)
        issues = ' '.join(str(item.get('issue', '')) for item in results)
        self.assertIn('wrongName', issues)

    def test_results_reset_between_runs(self):
        first = len(guidelines.check_odoo_python_standards('fixture_mod', self.path))
        second = len(guidelines.check_odoo_python_standards('fixture_mod', self.path))
        self.assertEqual(first, second)

    def test_own_module_scan(self):
        from odoo.modules import get_module_path
        path = get_module_path('odoo_health_report')
        results = guidelines.check_odoo_python_standards('odoo_health_report', path)
        self.assertIsInstance(results, list)
