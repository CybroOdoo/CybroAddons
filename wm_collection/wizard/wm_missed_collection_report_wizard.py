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
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WmMissedCollectionReportWizard(models.TransientModel):
    """Wizard to filter and generate the missed collections summary PDF report."""
    _name = 'wm.missed.collection.report.wizard'
    _description = 'Missed Collection Report Wizard'

    date_from = fields.Date(
        string='From', required=True,
        default=lambda self: fields.Date.context_today(self) - timedelta(days=7))
    date_to = fields.Date(
        string='To', required=True,
        default=lambda self: fields.Date.context_today(self))
    route_id = fields.Many2one('wm.route', string='Route', help='Provides information about route')
    reason_id = fields.Many2one('wm.missed.reason', string='Reason', help='Provides information about reason')

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        """
        Validate that Date To is not earlier than Date From.
        """
        for record in self:
            if record.date_from and record.date_to and record.date_to < record.date_from:
                raise ValidationError(_("To Date cannot be earlier than From Date."))

    def action_print_pdf(self):
        """
        Generate the missed collection summary report PDF for the selected
        period, listing all missed stops with reasons, partner contacts, and
        rescheduling instructions.
        """
        self.ensure_one()
        return self.env.ref(
            'wm_collection.action_report_wm_missed_collection'
        ).report_action(self)
