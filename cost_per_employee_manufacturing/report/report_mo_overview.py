# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
# ###############################################################################
from odoo import models


class ReportMoOverview(models.AbstractModel):
    """Override method for adding cost per employee"""
    _inherit = 'report.mrp.report_mo_overview'

    def _get_report_data(self, production_id):
        """Retrieves report data for the given production ID."""
        production = self.env['mrp.production'].browse(production_id)
        # Necessary to fetch the right quantities for multi-warehouse
        production = production.with_context(warehouse=production.warehouse_id.id)

        components = self._get_components_data(production, level=1, current_index='')
        operations = self._get_operations_data(production, level=1, current_index='')
        initial_mo_cost, initial_real_cost = self._compute_cost_sums(components, operations)
        remaining_cost_share, byproducts = self._get_byproducts_data(production, initial_mo_cost, initial_real_cost,
                                                                     level=1, current_index='')
        summary = self._get_mo_summary(production, components, initial_mo_cost, initial_real_cost, remaining_cost_share)
        cost_per_employee = {'cost_per_employe': production.cost_per_hour}
        extra_lines = self._get_report_extra_lines(summary, components, operations, cost_per_employee, production.state == 'done')
        report_values = {
            'id': production.id,
            'name': production.display_name,
            'summary': summary,
            'components': components,
            'operations': operations,
            'byproducts': byproducts,
            'extras': extra_lines,
            'cost_breakdown': self._get_cost_breakdown_data(production, extra_lines, remaining_cost_share),
            'cost_per_employ': production.cost_per_hour
        }
        return report_values

    def _get_report_extra_lines(self, summary, components, operations, cost_per_employee,production_done=False):
        """ Generates extra lines for the report, including cost per employee."""
        currency = summary.get('currency', self.env.company.currency_id)
        unit_mo_cost = currency.round(summary.get('mo_cost', 0) / (summary.get('quantity') or 1))
        unit_real_cost = currency.round(summary.get('real_cost', 0) / (summary.get('quantity') or 1))
        extras = {
            'unit_mo_cost': unit_mo_cost  + cost_per_employee['cost_per_employe'],
            'unit_mo_cost_decorator': self._get_comparison_decorator(unit_real_cost, unit_mo_cost, currency.rounding),
            'unit_real_cost': unit_real_cost+ cost_per_employee['cost_per_employe'],
        }
        if production_done:
            production_qty = summary.get('quantity') or 1.0
            extras['total_mo_cost_components'] = sum(
                compo.get('summary', {}).get('mo_cost', 0.0) for compo in components)
            extras['total_real_cost_components'] = sum(
                compo.get('summary', {}).get('real_cost', 0.0) for compo in components)
            extras['total_mo_cost_components_decorator'] = self._get_comparison_decorator(
                extras['total_real_cost_components'], extras['total_mo_cost_components'], currency.rounding)
            extras['unit_mo_cost_components'] = extras['total_mo_cost_components'] / production_qty
            extras['unit_real_cost_components'] = extras['total_real_cost_components'] / production_qty
            extras['total_mo_cost_operations'] = operations.get('summary', {}).get('mo_cost', 0.0)
            extras['total_real_cost_operations'] = operations.get('summary', {}).get('real_cost', 0.0)
            extras['total_mo_cost_operations_decorator'] = self._get_comparison_decorator(
                extras['total_real_cost_operations'], extras['total_mo_cost_operations'], currency.rounding)
            extras['unit_mo_cost_operations'] = extras['total_mo_cost_operations'] / production_qty
            extras['unit_real_cost_operations'] = extras['total_real_cost_operations'] / production_qty
            extras['total_mo_cost'] = extras['total_mo_cost_components'] + extras['total_mo_cost_operations']
            extras['total_real_cost'] = extras['total_real_cost_components'] + extras['total_real_cost_operations']
            extras['total_mo_cost_decorator'] = self._get_comparison_decorator(extras['total_real_cost'],
                                                                              extras['total_mo_cost'],currency.rounding)
        return extras
