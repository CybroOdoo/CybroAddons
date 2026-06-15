# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import io
from odoo import models, fields, api
from odoo.exceptions import UserError


# NHS brand colour
NHS_BLUE = '#005EB8'

# Column definitions: (header label, width in chars)
COLUMNS = [
    ('ODS Code',          10),
    ('Trust Name',        35),
    ('Short Name',        20),
    ('Health System',     14),
    ('Trust Type',        22),
    ('Foundation Trust',   8),
    ('Region',            25),
    ('ICB / Health Board', 38),
    ('CQC Rating',        22),
    ('Latest CQC Date',   15),
    ('Status',            14),
    ('Chair',             25),
    ('CEO',               25),
    ('Sites',              8),
    ('Departments',       12),
    ('Workforce (FTE)',   14),
    ('Bed Capacity',      14),
    ('Annual Budget (£)', 18),
    ('Surplus/Deficit (£)', 18),
    ('City',              20),
    ('Postcode',          12),
    ('Phone',             18),
    ('Website',           35),
]

RATING_LABELS = {
    'outstanding': 'Outstanding',
    'good': 'Good',
    'requires_improvement': 'Requires Improvement',
    'inadequate': 'Inadequate',
    'not_rated': 'Not Rated',
    False: '',
}

STATE_LABELS = {
    'draft': 'Draft',
    'under_review': 'Under Review',
    'active': 'Active',
    'special_measures': 'Special Measures',
    'merging': 'Merging',
    'dissolved': 'Dissolved',
}

HS_LABELS = {
    'nhs_england': 'NHS England',
    'nhs_scotland': 'NHS Scotland',
}


class NhsTrustDirectoryExport(models.TransientModel):
    _name = 'nhs.trust.directory.export'
    _description = 'NHS Trust Directory Excel Export'

    health_system = fields.Selection([
        ('all', 'All Systems'),
        ('nhs_england', 'NHS England Only'),
        ('nhs_scotland', 'NHS Scotland Only'),
    ],
        string='Health System',
        default='all',
        required=True,
        help="Filter export by health system."
    )
    status_filter = fields.Selection([
        ('all', 'All Statuses'),
        ('active', 'Active Trusts Only'),
        ('exclude_dissolved', 'Exclude Dissolved'),
    ],
        string='Status Filter',
        default='active',
        required=True,
        help="Filter by Trust workflow state."
    )
    region_ids = fields.Many2many(
        'nhs.region',
        string='Filter by Regions',
        help="Leave empty to include all regions. Select specific regions to limit the export."
    )
    export_file = fields.Binary(
        string='Excel File',
        readonly=True,
        help="Generated Excel file — click the download icon to save."
    )
    export_filename = fields.Char(
        string='Filename',
        readonly=True,
        default='NHS_Trust_Directory.xlsx'
    )

    # ── Onchange

    @api.onchange('health_system')
    def _onchange_health_system(self):
        self.region_ids = False

    # ── Domain helper

    def _build_domain(self):
        domain = []
        if self.health_system != 'all':
            domain.append(('health_system', '=', self.health_system))
        if self.status_filter == 'active':
            domain.append(('state', '=', 'active'))
        elif self.status_filter == 'exclude_dissolved':
            domain.append(('state', '!=', 'dissolved'))
        if self.region_ids:
            domain.append(('region_id', 'in', self.region_ids.ids))
        return domain

    # ── Export action ────────────────────────────────────────────────────────

    def action_export(self):
        self.ensure_one()
        try:
            import xlsxwriter  # noqa: F401
        except ImportError:
            raise UserError(
                'xlsxwriter is required for Excel export.\n'
                'Install it with: pip install xlsxwriter'
            )

        trusts = self.env['nhs.trust'].search(self._build_domain(), order='name')

        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})

        # ── Formats ──────────────────────────────────────────────────────────
        hdr_fmt = wb.add_format({
            'bold': True, 'bg_color': '#005EB8', 'font_color': '#FFFFFF',
            'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center',
        })
        cell_fmt = wb.add_format({'border': 1, 'text_wrap': True, 'valign': 'top'})
        num_fmt = wb.add_format({'border': 1, 'valign': 'top', 'num_format': '#,##0'})
        money_fmt = wb.add_format({'border': 1, 'valign': 'top', 'num_format': '£#,##0'})
        pos_fmt = wb.add_format({
            'border': 1, 'valign': 'top', 'num_format': '£#,##0', 'font_color': '#007700'
        })
        neg_fmt = wb.add_format({
            'border': 1, 'valign': 'top', 'num_format': '£#,##0', 'font_color': '#CC0000'
        })

        ws = wb.add_worksheet('NHS Trust Directory')
        ws.set_row(0, 32)
        ws.freeze_panes(1, 2)
        ws.autofilter(0, 0, 0, len(COLUMNS) - 1)

        # ── Header row
        for col, (label, width) in enumerate(COLUMNS):
            ws.write(0, col, label, hdr_fmt)
            ws.set_column(col, col, width)

        # ── Data rows
        for row_idx, trust in enumerate(trusts, start=1):
            icb_or_hb = (
                trust.icb_id.name
                if trust.health_system == 'nhs_england'
                else getattr(trust, 'health_board_id', self.env['nhs.health.board']).name
                if trust.health_system == 'nhs_scotland' else ''
            )
            surplus = getattr(trust, 'surplus_deficit', 0) or 0
            budget = getattr(trust, 'annual_budget', 0) or 0

            row = [
                trust.ods_code or '',
                trust.name or '',
                trust.short_name or '',
                HS_LABELS.get(trust.health_system, trust.health_system),
                trust.trust_type_id.name if trust.trust_type_id else '',
                'Yes' if trust.foundation_trust else 'No',
                trust.region_id.name if trust.region_id else '',
                icb_or_hb or '',
                RATING_LABELS.get(getattr(trust, 'latest_cqc_rating', False), ''),
                str(getattr(trust, 'latest_cqc_date', '') or ''),
                STATE_LABELS.get(trust.state, trust.state),
                trust.chair_id.name if trust.chair_id else '',
                trust.chief_executive_id.name if trust.chief_executive_id else '',
                getattr(trust, 'site_count', 0) or 0,
                getattr(trust, 'department_count', 0) or 0,
                getattr(trust, 'total_workforce', 0) or 0,
                getattr(trust, 'total_bed_capacity', 0) or 0,
                budget,
                surplus,
                trust.city or '',
                trust.zip or '',
                trust.phone or '',
                trust.website or '',
            ]

            for col, val in enumerate(row):
                if col == 17:  # Annual Budget
                    ws.write_number(row_idx, col, float(val or 0), money_fmt)
                elif col == 18:  # Surplus/Deficit
                    ws.write_number(row_idx, col, float(val or 0),
                                    pos_fmt if float(val or 0) >= 0 else neg_fmt)
                elif col in (13, 14, 15, 16):  # integer counts
                    ws.write_number(row_idx, col, int(val or 0), num_fmt)
                else:
                    ws.write(row_idx, col, str(val) if val else '', cell_fmt)

        wb.close()
        xlsx_bytes = base64.b64encode(output.getvalue())

        self.write({
            'export_file': xlsx_bytes,
            'export_filename': 'NHS_Trust_Directory.xlsx',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }
