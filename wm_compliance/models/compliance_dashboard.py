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
from datetime import date, datetime, timedelta

from odoo import api, models, _


class WmComplianceDashboard(models.AbstractModel):
    """Compliance dashboard backend model calculating permit expiries and target KPIs."""
    _name = 'wm.compliance.dashboard'
    _description = 'Waste Compliance Dashboard'

    @api.model
    def get_dashboard_data(self, timeframe='today'):
        """
        Return all KPI, chart, and alert data needed by the Compliance
        Dashboard OWL component.
        """
        has_manifest = 'wm.compliance.manifest' in self.env.registry
        has_document = 'wm.compliance.document' in self.env.registry
        has_target = 'wm.compliance.target' in self.env.registry
        has_certificate = 'wm.compliance.certificate' in self.env.registry
        has_facility = 'wm.disposal.facility' in self.env.registry

        can_access_manifest = has_manifest and self.env['wm.compliance.manifest'].has_access('read')
        can_access_document = has_document and self.env['wm.compliance.document'].has_access('read')
        can_access_target = has_target and self.env['wm.compliance.target'].has_access('read')
        can_access_certificate = has_certificate and self.env['wm.compliance.certificate'].has_access('read')
        can_access_facility = has_facility and self.env['wm.disposal.facility'].has_access('read')
        can_access_report = (
            'wm.compliance.report' in self.env.registry
            and self.env['wm.compliance.report'].has_access('create')
            and can_access_facility
        )

        company_ids = self.env.companies.ids or [self.env.company.id]
        company_domain = ['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]

        self = self.sudo()
        today = date.today()
        datetime.combine(today, datetime.max.time())
        seven_days_ago = today - timedelta(days=7)
        thirty_days_later = today + timedelta(days=30)

        # Determine timeframe date boundaries
        if timeframe == 'week':
            start_date = today - timedelta(days=6)
            prior_end_date = today - timedelta(days=7)
            prior_start_date = today - timedelta(days=13)
        elif timeframe == 'month':
            cur_month_start = date(today.year, today.month, 1)
            prior_end_date = cur_month_start - timedelta(days=1)
            prior_start_date = date(prior_end_date.year, prior_end_date.month, 1)
            start_date = cur_month_start
        else:  # today
            start_date = today
            prior_start_date = today - timedelta(days=1)
            prior_end_date = today - timedelta(days=1)

        # ── 1. MANIFESTS METRICS ──────────────────────────────────────────
        total_manifests = 0
        manifest_disposed = 0
        manifest_collected = 0
        manifest_submitted = 0
        manifest_draft = 0
        total_quantity_selected = 0.0
        manifest_transit_qty = 0.0
        manifest_disposed_qty = 0.0

        overdue_manifest_count = 0
        pending_custody_count = 0
        urgent_manifests = []

        if has_manifest:
            Manifest = self.env['wm.compliance.manifest']
            manifests_in_period = Manifest.search([
                ('manifest_date', '>=', start_date),
                ('manifest_date', '<=', today)
            ] + company_domain)

            # Active in-transit manifests (state = 'collected')
            active_in_transit_manifests = Manifest.search([('state', '=', 'collected')] + company_domain)
            manifest_transit_qty = round(sum(active_in_transit_manifests.mapped('total_quantity')), 2)

            manifests_to_count = manifests_in_period
            total_manifests = len(manifests_in_period)

            manifest_disposed = len(manifests_to_count.filtered(lambda m: m.state == 'disposed'))
            manifest_collected = len(manifests_to_count.filtered(lambda m: m.state == 'collected'))
            manifest_submitted = len(manifests_to_count.filtered(lambda m: m.state == 'submitted'))
            manifest_draft = len(manifests_to_count.filtered(lambda m: m.state == 'draft'))
            total_quantity_selected = round(sum(manifests_to_count.mapped('total_quantity')), 2)
            manifest_transit_qty = round(sum(manifests_to_count.filtered(lambda m: m.state == 'collected').mapped('total_quantity')), 2)
            manifest_disposed_qty = round(sum(manifests_to_count.filtered(lambda m: m.state == 'disposed').mapped('total_quantity')), 2)

            # Alerts: Overdue Manifests (submitted / collected > 7 days ago)
            overdue_records = Manifest.search([
                ('state', 'in', ['submitted', 'collected']),
                ('manifest_date', '<', seven_days_ago)
            ] + company_domain, order='manifest_date asc')
            overdue_manifest_count = len(overdue_records)

            # Alerts: Pending Custody Manifests (submitted with no custody entries)
            pending_custody_records = Manifest.search([
                ('state', 'in', ['submitted', 'collected']),
                ('custody_ids', '=', False)
            ] + company_domain, order='manifest_date asc')
            pending_custody_count = len(pending_custody_records)

            # Combined urgent manifests list (limit 8)
            seen_ids = set()
            for m in overdue_records:
                if m.id not in seen_ids:
                    seen_ids.add(m.id)
                    streams = m.line_ids.mapped('waste_category_id.name')
                    stream_str = ", ".join(filter(None, streams)) if streams else _('General')
                    urgent_manifests.append({
                        'id': m.id,
                        'name': m.name or f"MANIF-{m.id}",
                        'generator': m.generator_id.name or _('Unknown'),
                        'stream': stream_str,
                        'date': m.manifest_date.strftime('%Y-%m-%d') if m.manifest_date else '',
                        'state': m.state,
                        'issue': 'overdue',
                        'issue_label': _('Overdue (>7d)')
                    })

            for m in pending_custody_records:
                if m.id not in seen_ids and len(urgent_manifests) < 8:
                    seen_ids.add(m.id)
                    streams = m.line_ids.mapped('waste_category_id.name')
                    stream_str = ", ".join(filter(None, streams)) if streams else _('General')
                    urgent_manifests.append({
                        'id': m.id,
                        'name': m.name or f"MANIF-{m.id}",
                        'generator': m.generator_id.name or _('Unknown'),
                        'stream': stream_str,
                        'date': m.manifest_date.strftime('%Y-%m-%d') if m.manifest_date else '',
                        'state': m.state,
                        'issue': 'pending_custody',
                        'issue_label': _('No Custody Log')
                    })

        # ── 2. PERMITS & LICENCES (VAULT) ─────────────────────────────────
        total_vault_docs = 0
        expiring_docs_count = 0
        expired_docs_count = 0
        active_valid_docs_count = 0
        expiring_documents_list = []

        if has_document:
            Document = self.env['wm.compliance.document']
            total_vault_docs = Document.search_count(company_domain)

            expiring_docs_count = Document.search_count([
                ('expiry_date', '>=', today),
                ('expiry_date', '<=', thirty_days_later)
            ] + company_domain)

            expired_docs_count = Document.search_count([
                ('expiry_date', '<', today)
            ] + company_domain)

            active_valid_docs_count = Document.search_count([
                ('expiry_date', '>', thirty_days_later)
            ] + company_domain)

            # List of urgent documents (expired or expiring in 30 days)
            urgent_docs = Document.search([
                ('expiry_date', '<=', thirty_days_later)
            ] + company_domain, order='expiry_date asc', limit=8)

            type_selection_dict = dict(Document._fields['document_type'].selection) if 'document_type' in Document._fields else {}
            for doc in urgent_docs:
                days_left = (doc.expiry_date - today).days if doc.expiry_date else 0
                expiring_documents_list.append({
                    'id': doc.id,
                    'name': doc.name,
                    'type': type_selection_dict.get(doc.document_type, doc.document_type.capitalize() if doc.document_type else ''),
                    'expiry_date': doc.expiry_date.strftime('%Y-%m-%d') if doc.expiry_date else '',
                    'days_left': days_left,
                    'is_expired': days_left < 0,
                    'status_label': _('Expired') if days_left < 0 else (_('%d days left') % days_left if days_left > 0 else _('Expires Today'))
                })

        # ── 3. COMPLIANCE TARGETS METRICS ─────────────────────────────────
        targets_on_track = 0
        targets_at_risk = 0
        targets_breached = 0
        total_targets = 0
        avg_target_compliance = 0.0
        active_targets_list = []

        if has_target:
            Target = self.env['wm.compliance.target']
            targets = Target.search(company_domain)
            total_targets = len(targets)
            targets_on_track = len(targets.filtered(lambda t: t.state == 'on_track'))
            targets_at_risk = len(targets.filtered(lambda t: t.state == 'at_risk'))
            targets_breached = len(targets.filtered(lambda t: t.state == 'breached'))

            if total_targets > 0:
                avg_target_compliance = round(sum(targets.mapped('compliance_pct')) / total_targets, 1)

            # Key active targets
            for t in targets[:6]:
                active_targets_list.append({
                    'id': t.id,
                    'partner': t.partner_id.name or _('All Partners'),
                    'category': t.waste_category_id.name or _('All Streams'),
                    'target_qty': round(t.target_quantity, 2),
                    'achieved_qty': round(t.achieved_quantity, 2),
                    'compliance_pct': round(t.compliance_pct, 1),
                    'state': t.state
                })

        # ── 4. CERTIFICATES & SIGNATURES ─────────────────────────────────
        total_certificates = 0
        certificates_issued = 0
        certificates_draft = 0
        certificates_verified = 0

        if has_certificate:
            Certificate = self.env['wm.compliance.certificate']
            total_certificates = Certificate.search_count(company_domain)
            certificates_issued = Certificate.search_count(company_domain + [('state', '=', 'issued')])
            certificates_draft = Certificate.search_count(company_domain + [('state', '=', 'draft')])
            certs_with_sig = Certificate.search(company_domain + [('signature_id', '!=', False)])
            certificates_verified = sum(1 for c in certs_with_sig if c.signature_hash_verified)

        # ── 5. DISPOSAL FACILITIES ────────────────────────────────────────
        facility_count = self.env['wm.disposal.facility'].search_count(company_domain) if has_facility else 0

        # ── 6. STREAM DISTRIBUTION & CHART METRICS ───────────────────────
        stream_labels = []
        stream_selected_qty = []
        stream_prior_qty = []
        stream_data = []
        total_stream_qty = 0.0

        if has_manifest:
            ManifestLine = self.env['wm.compliance.manifest.line']
            selected_lines = ManifestLine.search([
                ('manifest_id.manifest_date', '>=', start_date),
                ('manifest_id.manifest_date', '<=', today),
                ('manifest_id.company_id', 'in', company_ids)
            ])
            prior_lines = ManifestLine.search([
                ('manifest_id.manifest_date', '>=', prior_start_date),
                ('manifest_id.manifest_date', '<=', prior_end_date),
                ('manifest_id.company_id', 'in', company_ids)
            ])

            categories = self.env['wm.waste.category'].search([], order='sequence, id')
            if not categories:
                cat_ids = (selected_lines.mapped('waste_category_id') | prior_lines.mapped('waste_category_id')).ids
                categories = self.env['wm.waste.category'].browse(cat_ids)

            colors_palette = ['#EF4444', '#F97316', '#3B82F6', '#EAB308', '#10B981', '#8B5CF6', '#EC4899', '#06B6D4', '#64748B']

            selected_qty_by_cat = {}
            for line in selected_lines:
                cat = line.waste_category_id
                if cat:
                    selected_qty_by_cat[cat.id] = selected_qty_by_cat.get(cat.id, 0.0) + (line.quantity or 0.0)

            prior_qty_by_cat = {}
            for line in prior_lines:
                cat = line.waste_category_id
                if cat:
                    prior_qty_by_cat[cat.id] = prior_qty_by_cat.get(cat.id, 0.0) + (line.quantity or 0.0)

            total_stream_qty = round(sum(selected_qty_by_cat.values()), 2)

            # Sort categories: active categories with quantity > 0 first, then by sequence
            categories_sorted = sorted(
                categories,
                key=lambda c: (
                    0 if selected_qty_by_cat.get(c.id, 0.0) > 0 else 1,
                    -selected_qty_by_cat.get(c.id, 0.0),
                    getattr(c, 'sequence', 99) or 99,
                    c.name or ''
                )
            )

            for idx, cat in enumerate(categories_sorted):
                cat_sel_qty = round(selected_qty_by_cat.get(cat.id, 0.0), 2)
                cat_prior_qty = round(prior_qty_by_cat.get(cat.id, 0.0), 2)
                stream_labels.append(cat.name)
                stream_selected_qty.append(cat_sel_qty)
                stream_prior_qty.append(cat_prior_qty)

                pct = round((cat_sel_qty / total_stream_qty * 100.0), 1) if total_stream_qty > 0 else 0.0
                stream_data.append({
                    'name': cat.name,
                    'code': cat.code or f"cat_{cat.id}",
                    'quantity': cat_sel_qty,
                    'percentage': pct,
                    'color': colors_palette[idx % len(colors_palette)],
                })

        return {
            'timeframe': timeframe,
            'company_name': self.env.company.name,
            'facility_count': facility_count,

            # Manifests
            'total_manifests': total_manifests,
            'manifest_disposed': manifest_disposed,
            'manifest_collected': manifest_collected,
            'manifest_submitted': manifest_submitted,
            'manifest_draft': manifest_draft,
            'total_quantity_selected': round(total_quantity_selected, 2),
            'manifest_transit_qty': round(manifest_transit_qty, 2),
            'manifest_disposed_qty': round(manifest_disposed_qty, 2),

            # Alerts
            'overdue_manifest_count': overdue_manifest_count,
            'pending_custody_count': pending_custody_count,
            'total_alerts_count': overdue_manifest_count + pending_custody_count + expired_docs_count,
            'urgent_manifests': urgent_manifests,

            # Vault Documents
            'total_vault_docs': total_vault_docs,
            'expiring_docs_count': expiring_docs_count,
            'expired_docs_count': expired_docs_count,
            'active_valid_docs_count': active_valid_docs_count,
            'expiring_documents_list': expiring_documents_list,

            # Targets
            'total_targets': total_targets,
            'targets_on_track': targets_on_track,
            'targets_at_risk': targets_at_risk,
            'targets_breached': targets_breached,
            'avg_target_compliance': avg_target_compliance,
            'active_targets_list': active_targets_list,

            # Certificates
            'total_certificates': total_certificates,
            'certificates_issued': certificates_issued,
            'certificates_draft': certificates_draft,
            'certificates_verified': certificates_verified,

            # Chart Data
            'stream_labels': stream_labels,
            'stream_selected_qty': stream_selected_qty,
            'stream_prior_qty': stream_prior_qty,
            'stream_data': stream_data,
            'total_stream_qty': total_stream_qty,

            # Permissions
            'can_access_manifest': can_access_manifest,
            'can_access_document': can_access_document,
            'can_access_target': can_access_target,
            'can_access_certificate': can_access_certificate,
            'can_access_facility': can_access_facility,
            'can_access_report': can_access_report,
        }
