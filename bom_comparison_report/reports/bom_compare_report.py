#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, models


class BomCompareReport(models.AbstractModel):
    """Values of the BoM comparison report."""
    _name = 'report.bom_comparison_report.bom_compare_report'
    _description = 'BoM Comparison Report'

    @api.model
    def _get_report_values(self, docids, data=None):  # pylint: disable=unused-argument
        """Return the comparison of each wizard."""
        wizards = self.env['bom.comparison'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'bom.comparison',
            'docs': wizards,
            'comparisons': {
                wizard.id: wizard._get_comparison_lines()
                for wizard in wizards},
            'currency': self.env.company.currency_id,
        }
