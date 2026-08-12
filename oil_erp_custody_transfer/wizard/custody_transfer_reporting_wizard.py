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
# ############################################################################
import json
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CustodyTransferReportingWizard(models.TransientModel):
    _name = 'custody.transfer.reporting.wizard'
    _description = 'Custody Transfer Reporting Wizard'

    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')

    picking_type_id = fields.Many2one('stock.picking.type', string='Operation Type')
    transfer_purpose = fields.Selection([
        ('commercial_sale', 'Commercial Sale'),
        ('inter_facility', 'Inter-Facility Transfer'),
        ('emergency', 'Emergency Transfer'),
        ('intercompany', 'Intercompany'),
        ('pipeline_injection', 'Pipeline Injection'),
        ('other', 'Other'),
    ], string='Transfer Purpose')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('disputed', 'Disputed'),
    ], string='Status')
    owner_partner_id = fields.Many2one('res.partner', string='Legal Owner')
    custodian_partner_id = fields.Many2one('res.partner', string='Custodian')
    carrier_partner_id = fields.Many2one('res.partner', string='Carrier')

    def _get_domain(self):
        self.ensure_one()
        domain = []
        if self.date_from:
            domain.append(('transfer_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('transfer_date', '<=', self.date_to))
        if self.picking_type_id:
            domain.append(('picking_type_id', '=', self.picking_type_id.id))
        if self.transfer_purpose:
            domain.append(('transfer_purpose', '=', self.transfer_purpose))
        if self.state:
            domain.append(('state', '=', self.state))
        if self.owner_partner_id:
            domain.append(('owner_partner_id', '=', self.owner_partner_id.id))
        if self.custodian_partner_id:
            domain.append(('custodian_partner_id', '=', self.custodian_partner_id.id))
        if self.carrier_partner_id:
            domain.append(('carrier_partner_id', '=', self.carrier_partner_id.id))
        return domain

    def get_report_records(self):
        self.ensure_one()
        return self.env['custody.transfer'].search(self._get_domain())

    def get_filters_basis(self):
        self.ensure_one()
        basis = [('Report', 'Custody Transfer Report')]
        if self.date_from:
            basis.append(('Start Date', self.date_from.strftime('%Y-%m-%d')))
        if self.date_to:
            basis.append(('End Date', self.date_to.strftime('%Y-%m-%d')))
        if self.picking_type_id:
            basis.append(('Operation Type', self.picking_type_id.name))
        if self.transfer_purpose:
            basis.append(('Purpose', dict(self._fields['transfer_purpose'].selection).get(self.transfer_purpose)))
        if self.state:
            basis.append(('Status', dict(self._fields['state'].selection).get(self.state)))
        if self.owner_partner_id:
            basis.append(('Legal Owner', self.owner_partner_id.name))
        if self.custodian_partner_id:
            basis.append(('Custodian', self.custodian_partner_id.name))
        if self.carrier_partner_id:
            basis.append(('Carrier', self.carrier_partner_id.name))
        return basis

    def get_filters_basis_chunks(self):
        basis = self.get_filters_basis()
        chunk_size = 3
        return [basis[i:i + chunk_size] for i in range(0, len(basis), chunk_size)]

    def action_print_pdf(self):
        self.ensure_one()
        records = self.get_report_records()
        if not records:
            raise ValidationError(_("No records found matching the selected criteria."))
        return self.env.ref(
            'oil_erp_custody_transfer.action_report_custody_transfer_pdf'
        ).report_action(self)

    def action_print_xlsx(self):
        self.ensure_one()
        records = self.get_report_records()
        if not records:
            raise ValidationError(_("No records found matching the selected criteria."))
        domain = self._get_domain()
        url = f'/oil_erp_custody_transfer/report_xlsx?domain={json.dumps(domain, default=str)}'
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
        }
