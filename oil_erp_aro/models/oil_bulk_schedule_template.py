# -*- coding: utf-8 -*-
#############################################################################
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

from odoo import api, fields, models
from odoo.tools.translate import _

ARO_TARGETS = {
    'oil.aro.obligation': {
        'action_type': 'create_record',
        'source_model': 'oil.reservoir',
    },
    'oil.aro.accretion.line': {
        'action_type': 'edit_record',
        'source_model': 'oil.aro.obligation',
    },
}


class OilBulkScheduleTemplate(models.Model):
    _inherit = 'oil.bulk.schedule.template'

    # ── Target 1: obligation creation ──────────────────────────────────
    aro_template_id = fields.Many2one(
        'oil.aro.template',
        string='ARO Configuration Template',
        help='ARO config template stamped on every created obligation — '
             'accounts, discount rate and accretion frequency. Required when '
             'creating obligations.',
    )
    aro_asset_kind = fields.Selection(
        [
            ('reservoir', 'Reservoir / Well'),
            ('lease', 'Lease'),
        ],
        string='ARO Asset Kind',
        default='reservoir',
        help='Source of the obligations to create. Reservoir reads the '
             'estimated decommissioning cost and abandonment date from the '
             'well; Lease reads the lease end date.',
    )
    # ── Target 2: accretion posting ────────────────────────────────────
    aro_accretion_frequency = fields.Selection(
        [
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('annual', 'Annual'),
        ],
        string='ARO Accretion Frequency',
        help='Filter: only post accretion for obligations with this '
             'accretion frequency. Leave empty for all frequencies.',
    )
    aro_posting_date = fields.Date(
        string='ARO Posting Date',
        help='Override the posting date for accretion. Defaults to the job '
             'scheduled date, then today, when empty.',
    )
    # ── Shared scope filter (replaces the planned oil.field filter, which
    #    has no model in this code base) ──────────────────────────────────
    aro_reservoir_ids = fields.Many2many(
        'oil.reservoir',
        'oil_bulk_template_aro_reservoir_rel',
        'template_id',
        'reservoir_id',
        string='ARO Reservoirs',
        help='Scope filter. For obligation creation, limit to these '
             'reservoirs; for accretion posting, limit to obligations on '
             'these reservoirs. Leave empty for no reservoir restriction.',
    )

    @api.model
    def _bulk_target_registry(self):
        """Executes the 'bulk target registry' process within the operational workflow."""
        registry = super()._bulk_target_registry()
        registry.update(ARO_TARGETS)
        return registry

    def _bulk_resolve_source_records(self, domain, limit=None):
        """Executes the 'bulk resolve source records' process within the operational workflow."""
        self.ensure_one()
        target = self.target_model_name
        if target == 'oil.aro.obligation':
            return self._bulk_resolve_aro_create_sources(domain, limit=limit)
        if target == 'oil.aro.accretion.line':
            return self._bulk_resolve_aro_accretion_sources(domain, limit=limit)
        return super()._bulk_resolve_source_records(domain, limit=limit)

    def _bulk_resolve_aro_create_sources(self, domain, limit=None):
        """Executes the 'bulk resolve aro create sources' process within the operational workflow."""
        search_domain = list(domain)
        if (self.aro_asset_kind or 'reservoir') == 'lease':
            model = self.env['oil.lease.agreement']
            search_domain += [
                ('state', '=', 'active'),
                ('aro_obligation_ids', '=', False),
            ]
        else:
            model = self.env['oil.reservoir']
            search_domain += [
                ('aro_required', '=', True),
                ('aro_obligation_ids', '=', False),
            ]
            if self.aro_reservoir_ids:
                search_domain += [('id', 'in', self.aro_reservoir_ids.ids)]
        if 'company_id' in model._fields:
            search_domain += [('company_id', '=', self.env.company.id)]
        return model.search(search_domain, limit=limit)

    def _bulk_resolve_aro_accretion_sources(self, domain, limit=None):
        """Executes the 'bulk resolve aro accretion sources' process within the operational workflow."""
        model = self.env['oil.aro.obligation']
        search_domain = list(domain)
        search_domain += [('state', 'in', ('recognized', 'executing'))]
        if self.aro_accretion_frequency:
            search_domain += [
                ('accretion_frequency', '=', self.aro_accretion_frequency),
            ]
        if self.aro_reservoir_ids:
            search_domain += [('reservoir_id', 'in', self.aro_reservoir_ids.ids)]
        if 'company_id' in model._fields:
            search_domain += [('company_id', '=', self.env.company.id)]
        return model.search(search_domain, limit=limit)

    def _bulk_conflict_warnings(self):
        """Executes the 'bulk conflict warnings' process within the operational workflow."""
        warnings = super()._bulk_conflict_warnings()
        if self.target_model_name == 'oil.aro.accretion.line' and \
                not self.aro_posting_date:
            warnings.append(_(
                'Accretion postings will use the job date (today, if run now) '
                'as the posting date unless an ARO Posting Date is set on the '
                'template. Verify the date before confirming.',
            ))
        return warnings
