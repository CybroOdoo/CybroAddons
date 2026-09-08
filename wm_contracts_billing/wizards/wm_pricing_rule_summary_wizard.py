# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import io

from odoo import fields, models, _
from odoo.exceptions import UserError


try:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
except ImportError:
    openpyxl = None


class WmPricingRuleSummaryWizard(models.TransientModel):
    """Wizard to generate Pricing Rule Summary report as PDF or XLSX."""
    _name = 'wm.pricing.rule.summary.wizard'
    _description = 'Pricing Rule Summary Wizard'

    output_type = fields.Selection([
        ('pdf', 'PDF Document'),
        ('xlsx', 'Excel Spreadsheet (.xlsx)')
    ], string='Report Format', default='pdf', required=True)
    rule_ids = fields.Many2many('wm.pricing.rule', string='Pricing Rules')
    data_file = fields.Binary(string='File', readonly=True)
    filename = fields.Char(string='Filename', readonly=True)

    def action_generate_report(self):
        """
        Render the pricing rule summary report PDF showing all active rate
        configurations, minimum charges, and applicable contract types for
        management review.
        """
        self.ensure_one()
        rules = self.rule_ids or self.env['wm.pricing.rule'].search([('active', '=', True)])
        rules = rules.sorted(key=lambda r: (r.waste_category_id.name or '', r.sequence))

        if self.output_type == 'pdf':
            return self.env.ref('wm_contracts_billing.action_report_pricing_rule_summary').report_action(rules)

        elif self.output_type == 'xlsx':
            if not openpyxl:
                raise UserError(_("The openpyxl library is required for Excel export."))

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Pricing Rule Summary"

            # Header Style
            header_fill = PatternFill(start_color="005B1F", end_color="005B1F", fill_type="solid")
            header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
            center_align = Alignment(horizontal="center", vertical="center")
            left_align = Alignment(horizontal="left", vertical="center")
            right_align = Alignment(horizontal="right", vertical="center")

            headers = ["Category", "Customer", "Price per kg", "Min Weight (kg)", "Min Charge", "Effective Date", "Expiry Date"]
            ws.append(headers)

            for col_num in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=col_num)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = center_align

            row_idx = 2
            for rule in rules:
                category_name = rule.waste_category_id.name or ''
                partner_name = rule.partner_id.name or 'All Customers'
                price_kg = rule.price_per_kg or 0.0
                min_wt = rule.min_weight or 0.0
                min_chg = rule.min_charge or 0.0
                eff_date = rule.effective_date.strftime('%Y-%m-%d') if rule.effective_date else ''
                exp_date = rule.expiry_date.strftime('%Y-%m-%d') if rule.expiry_date else ''

                ws.append([category_name, partner_name, price_kg, min_wt, min_chg, eff_date, exp_date])

                ws.cell(row=row_idx, column=1).alignment = left_align
                ws.cell(row=row_idx, column=2).alignment = left_align
                ws.cell(row=row_idx, column=3).alignment = right_align
                ws.cell(row=row_idx, column=4).alignment = right_align
                ws.cell(row=row_idx, column=5).alignment = right_align
                ws.cell(row=row_idx, column=6).alignment = center_align
                ws.cell(row=row_idx, column=7).alignment = center_align
                row_idx += 1

            # Auto-fit column widths
            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

            output = io.BytesIO()
            wb.save(output)
            out_bytes = output.getvalue()
            output.close()

            self.write({
                'data_file': base64.b64encode(out_bytes),
                'filename': 'Pricing_Rule_Summary.xlsx'
            })

            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/?model=wm.pricing.rule.summary.wizard&id={self.id}&field=data_file&filename_field=filename&download=true',
                'target': 'self',
            }
