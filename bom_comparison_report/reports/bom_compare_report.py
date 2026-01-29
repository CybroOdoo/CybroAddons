# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, models


class BomCompareReport(models.AbstractModel):
    """Abstract model for the pdf"""
    _name = 'report.bom_comparison_report.bom_compare_report'
    _description = 'Model Used To Print Bom Comparison Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """To get the report values"""

        analysis = data['form_data']['analysis']
        product_unit = data['form_data']['product_unit']
        bom_report = []
        for line in data['form_data']['bom_ids']:
            bom = self.env['mrp.bom'].browse(line)
            bom_total = 0
            for record in bom.bom_line_ids:
                price = record.product_id.lst_price if analysis == 'sale_price' else record.product_id.standard_price
                bom_total += (record.product_qty * price)
            unit_total = (bom_total / bom.product_qty) if bom.product_qty else 0

            bom_details = {
                'bom_name': bom.display_name,
                'products': len(bom.bom_line_ids.ids),
                'total': unit_total,
                'total_given': unit_total * product_unit
            }
            bom_report.append(bom_details)
        better_option = bom_report[min(range(len(bom_report)), key=lambda i: bom_report[i]['total_given'])]
        data = {
            'analysis': analysis,
            'unit': product_unit,
            'bom_report': bom_report,
            'better_option': better_option,
            'currency': self.env.user.company_id.currency_id.symbol,
        }
        return {
            'doc_ids': docids,
            'doc_model': 'bom.compare.wizard',
            'data': data,
        }
