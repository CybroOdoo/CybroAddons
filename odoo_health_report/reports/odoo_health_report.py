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
import copy
from odoo import api,models


class OdooHealthReport(models.AbstractModel):
    """Generate module health report data for QWeb PDF reports."""
    _name = "report.odoo_health_report.odoo_health_report"
    _description = "Odoo Health Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        module_quality_dict = {}
        selected_modules = []
        data_dict = data.get('context', {}).get('data') or data
        if 'module' in data_dict.get('selected'):
            ModuleQualityPackage = self.env['module.quality.package']
            module_quality_dict['field_details'] = ModuleQualityPackage.fields_and_apps_overview()
            module_quality_dict['count_lines'] = ModuleQualityPackage.count_lines_of_code_in_modules()

            selected_modules = [key for key, value in data_dict.get('module_selected', {}).items() if value]

            violations_list = []
            if selected_modules:
                for selected_module in selected_modules:
                    module_violations = ModuleQualityPackage.check_violations_report(selected_module)
                    violations_list.append(copy.deepcopy(module_violations))
            else:
                all_installed_modules = ModuleQualityPackage.get_installed_modules().mapped('name')
                for module in all_installed_modules:
                    violations_list.append(ModuleQualityPackage.check_violations_report(module))
            module_quality_dict['violations'] = violations_list
        else:
            module_quality_dict = None

        return {
            'module_quality': module_quality_dict,
            'doc_ids': docids,
            'doc_model': 'module.quality.package',
            'docs': self,
            'selected_module': selected_modules
        }
