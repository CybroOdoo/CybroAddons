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
from collections import defaultdict

from odoo import api, models


class WmMissedCollectionReport(models.AbstractModel):
    """Read-only report model aggregating missed collection events by reason, zone, and time period."""
    _name = 'report.wm_collection.report_missed_collection_document'
    _description = 'Missed Collection Report'

    def _build_group(self, records, field_name, name_getter):
        """
        Group missed collection records by partner, reason, or zone as
        specified in the report configuration, creating the section-level
        subtotal rows for the PDF output.
        """
        counts = defaultdict(lambda: {'count': 0, 'label': ''})
        for rec in records:
            related = getattr(rec, field_name)
            key = related.id if related else 0
            counts[key]['count'] += 1
            counts[key]['label'] = name_getter(related) or 'Unassigned'
        rows = [
            {'label': data['label'], 'count': data['count']}
            for key, data in counts.items()
        ]
        rows.sort(key=lambda r: r['count'], reverse=True)
        return rows

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Fetch and structure the missed collection data for the QWeb report
        renderer, applying date range and reason filters before passing the
        dataset to the report template.
        """
        wizards = self.env['wm.missed.collection.report.wizard'].browse(docids)
        report_data = {}

        for wizard in wizards:
            domain = [
                ('missed_date', '>=', wizard.date_from),
                ('missed_date', '<=', wizard.date_to),
            ]
            if wizard.route_id:
                domain.append(('route_id', '=', wizard.route_id.id))
            if wizard.reason_id:
                domain.append(('reason_id', '=', wizard.reason_id.id))

            records = self.env['wm.missed.collection'].search(
                domain, order='missed_date')

            report_data[wizard.id] = {
                'records': records,
                'total': len(records),
                'not_notified': len(records.filtered(
                    lambda r: not r.customer_notified)),
                'by_reason': self._build_group(
                    records, 'reason_id', lambda r: r.name),
                'by_customer': self._build_group(
                    records, 'partner_id', lambda r: r.display_name),
                'by_route': self._build_group(
                    records, 'route_id', lambda r: r.display_name),
            }

        return {
            'doc_ids': docids,
            'doc_model': 'wm.missed.collection.report.wizard',
            'docs': wizards,
            'report_data': report_data,
        }
