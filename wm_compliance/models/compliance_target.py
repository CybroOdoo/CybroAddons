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
from odoo import api, fields, models, _


class ComplianceTarget(models.Model):
    """Environmental compliance target tracking waste diversion and recycling quotas."""
    _name = 'wm.compliance.target'
    _description = 'Compliance Target'
    _order = 'period_end desc, id desc'

    partner_id = fields.Many2one('res.partner', string='Responsible Partner', required=True)
    partner_role = fields.Selection([
        ('generator', 'Generator (Customer)'),
        ('transporter', 'Transporter'),
        ('any', 'Any Role (Generator / Transporter)')
    ], string='Partner Role', default='generator', required=True)
    waste_category_id = fields.Many2one('wm.waste.category', string='Waste Category', help="Leave blank to track all categories.")
    period_start = fields.Date(string='Period Start', required=True)
    period_end = fields.Date(string='Period End', required=True)
    target_quantity = fields.Float(string='Target Quantity', required=True, default=0.0)

    achieved_quantity = fields.Float(
        string='Achieved Quantity',
        compute='_compute_achieved_quantity',
        store=True
    )
    compliance_pct = fields.Float(
        string='Compliance %',
        compute='_compute_achieved_quantity',
        store=True
    )
    state = fields.Selection([
        ('on_track', 'On Track (>=80%)'),
        ('at_risk', 'At Risk (50-80%)'),
        ('breached', 'Breached (<50%)')
    ], string='Status', compute='_compute_achieved_quantity', store=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    def _compute_display_name(self):
        """
        Construct the compliance target display name from the regulatory period
        and waste category, used in breadcrumbs and Many2one dropdown
        selections.
        """
        for rec in self:
            partner_name = rec.partner_id.name or _("Unknown Partner")
            cat_name = rec.waste_category_id.name or _("All Categories")
            start = rec.period_start.strftime('%b %d, %Y') if rec.period_start else ''
            end = rec.period_end.strftime('%b %d, %Y') if rec.period_end else ''
            period = f"{start} - {end}" if start and end else (start or end or "")
            rec.display_name = f"{partner_name} - {cat_name} ({period})" if period else f"{partner_name} - {cat_name}"

    @api.depends('partner_id', 'waste_category_id', 'period_start', 'period_end', 'target_quantity')
    def _compute_achieved_quantity(self):
        """
        Aggregate approved manifest quantities for the target's waste category
        within the compliance reporting period, calculating the progress toward
        the regulatory target.
        """
        for rec in self:
            if not rec.partner_id or not rec.period_start or not rec.period_end:
                rec.achieved_quantity = 0.0
                rec.compliance_pct = 0.0
                rec.state = 'breached'
                continue

            # Sum quantity of lines of manifests in submitted/collected/disposed state within the period
            domain = [
                ('manifest_id.state', 'in', ['submitted', 'collected', 'disposed']),
                ('manifest_id.manifest_date', '>=', rec.period_start),
                ('manifest_id.manifest_date', '<=', rec.period_end)
            ]
            if rec.partner_role == 'generator':
                domain.append(('manifest_id.generator_id', '=', rec.partner_id.id))
            elif rec.partner_role == 'transporter':
                domain.append(('manifest_id.transporter_id', '=', rec.partner_id.id))
            else:  # any role
                domain.append('|')
                domain.append(('manifest_id.generator_id', '=', rec.partner_id.id))
                domain.append(('manifest_id.transporter_id', '=', rec.partner_id.id))

            if rec.waste_category_id:
                domain.append(('waste_category_id', '=', rec.waste_category_id.id))

            lines = self.env['wm.compliance.manifest.line'].search(domain)
            rec.achieved_quantity = sum(lines.mapped('quantity'))

            if rec.target_quantity > 0:
                rec.compliance_pct = (rec.achieved_quantity / rec.target_quantity) * 100.0
            else:
                rec.compliance_pct = 100.0

            if rec.compliance_pct >= 80.0:
                rec.state = 'on_track'
            elif rec.compliance_pct >= 50.0:
                rec.state = 'at_risk'
            else:
                rec.state = 'breached'
