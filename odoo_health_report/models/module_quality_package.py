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
import os
from collections import defaultdict, Counter
from pathlib import Path

from odoo import api, models
from odoo import modules
from odoo.modules import get_modules, get_module_path
from . import check_violations


class ModuleQuality(models.AbstractModel):
    """Class for analyzing the quality of installed modules"""
    _name = 'module.quality.package'
    _description = "Module Quality Metrics"

    def get_installed_modules(self):
        """Function to fetch installed modules"""
        return self.env['ir.module.module'].search([
            ('state', '=', 'installed'),
            ('name', '!=', 'odoo_health_report')
        ])

    @api.model
    def count_lines_of_code_in_modules(self):
        """Count lines of Python, JavaScript, and XML code in all installed Odoo modules."""
        module_ids = self.get_installed_modules()
        total_lines = Counter()
        exclude_files = {'__init__.py', '__manifest__.py'}
        result = defaultdict(list)

        for module in module_ids:
            module_name = module.name
            author = module.author
            module_path = get_module_path(module_name)
            if not module_path:
                continue
            loc = Counter({'.py': 0, '.js': 0, '.xml': 0})
            for ext in loc:
                for file in Path(module_path).rglob(f'*{ext}'):
                    if file.name in exclude_files:
                        continue
                    try:
                        with file.open('r', encoding='utf-8', errors='ignore') as f:
                            loc[ext] += sum(1 for _ in f)
                    except (IOError, UnicodeDecodeError):
                        continue

            result[author].append({
                'technical_name': module_name,
                'module_name': module.display_name,
                'py_lines': loc['.py'],
                'js_lines': loc['.js'],
                'xml_lines': loc['.xml']
            })
            total_lines.update({
                'py_lines': loc['.py'],
                'js_lines': loc['.js'],
                'xml_lines': loc['.xml']
            })
        return {'result': dict(result), 'total_lines': dict(total_lines)}

    @api.model
    def fields_and_apps_overview(self):
        """Get the count of fields in database"""
        # apps in percentage
        all_apps = self.env['ir.module.module'].search_count([])
        installed_apps = self.env['ir.module.module'].search_count([('state', '=', 'installed')])
        percentage = (installed_apps/all_apps) * 100

        total = self.env['ir.model.fields'].search([])
        non_stored = len(total.filtered(lambda x: not x.store))
        model_stored = len(total.filtered(lambda x: x.store))

        return {
            "critical_overview": {
                "overall_percentage": {
                    "label": "Overall Apps Installed ratio",
                    "value": round(percentage, 2),
                    "description": "Displays the percentage of installed apps in Odoo compared to the total available apps."
                },
                "total_fields": {
                    "label": "Total fields",
                    "value": len(total),
                    "description": "shows the total number of fields",
                },
                "stored": {
                    "label": "Stored fields",
                    "value": model_stored,
                    "description":
                        "Shows the total count of stored fields in the database",
                },
                "non_stored": {
                    "label": "Non stored fields",
                    "value": non_stored,
                    "description": "Shows the total count of non-stored fields in the database",
                },
            },
        }

    @api.model
    def get_module_and_icons(self):
        """Retrieve all custom module name and icon as a dictionary"""
        module_and_icon = {}
        is_updated = self.env['base.module.update'].search([], limit=1, order='id desc')
        if not is_updated:
            is_updated = self.env['base.module.update'].create({})
        is_updated.update_module()

        for module in get_modules():
            if module != 'odoo_health_report':
                module_name = self.env.ref(f'base.module_{module}').display_name
                module_icon = modules.module.get_module_icon(module)
                module_and_icon[module] = [module_name, module_icon]
        return module_and_icon

    @api.model
    def check_violations_report(self, module):
        """Check the violations for PDF report"""
        return check_violations.violations_report(self, module)

    @api.model
    def check_violations(self, module):
        """Check the violations and standards"""
        return check_violations.get_violations(module)