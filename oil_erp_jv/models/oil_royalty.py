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
from odoo.exceptions import UserError


class OilRoyalty(models.Model):
    """Extends oil.royalty to link with JV Agreements and enable
    direct creation of JV Revenue Distributions from confirmed royalties."""
    _inherit = 'oil.royalty'

    jv_agreement_id = fields.Many2one(
        'oil.jv.agreement',
        string='JV Agreement',
        domain="[('id', 'in', allowed_jv_agreement_ids)]",
        help="Joint Operating Agreement associated with this royalty.")
    allowed_jv_agreement_ids = fields.Many2many(
        'oil.jv.agreement',
        string='Allowed JV Agreements',
        compute='_compute_allowed_jv_agreement_ids',
        help="Active JV agreements available for the selected lease.")
    jv_revenue_count = fields.Integer(
        string='JV Revenue Distributions',
        compute='_compute_jv_revenue_count')
    jv_bill_ids = fields.Many2many(
        'account.move',
        string='JV Bills',
        compute='_compute_jv_bills',
        help="All vendor bills generated via the JV Revenue Distribution.")
    jv_bill_count = fields.Integer(
        string='JV Bill Count',
        compute='_compute_jv_bills')
    expiry_warning = fields.Text(
        string='Expiry Warning',
        compute='_compute_expiry_warning',
        help="Warning if related lease or JV agreement has expired.")

    @api.depends('lease_id', 'lease_id.reservoir_ids', 'lease_id.reservoir_ids.project_id')
    def _compute_allowed_jv_agreement_ids(self):
        """Restrict JV agreements to the projects linked to the selected lease."""
        Agreement = self.env['oil.jv.agreement']
        for record in self:
            if not record.lease_id:
                record.allowed_jv_agreement_ids = Agreement.search([
                    ('state', '=', 'active'),
                ])
                continue

            project_ids = record.lease_id.reservoir_ids.mapped('project_id').ids
            domain = [('state', '=', 'active')]
            if project_ids:
                domain.append(('project_id', 'in', project_ids))
            else:
                domain.append(('id', '=', False))
            record.allowed_jv_agreement_ids = Agreement.search(domain)

    @api.onchange('lease_id')
    def _onchange_lease_id(self):
        """Clear JV agreement if it no longer matches the selected lease."""
        if (self.jv_agreement_id
                and self.jv_agreement_id not in self.allowed_jv_agreement_ids):
            self.jv_agreement_id = False

    def _compute_expiry_warning(self):
        """Shows warnings if related lease or JV agreement has expired."""
        for record in self:
            warnings = []
            if record.lease_id and record.lease_id.state == 'expired':
                warnings.append(
                    _("Lease Agreement '%s' has expired.",
                      record.lease_id.name))
            if (record.jv_agreement_id
                    and record.jv_agreement_id.state == 'expired'):
                warnings.append(
                    _("JV Agreement '%s' has expired.",
                      record.jv_agreement_id.name))
            record.expiry_warning = (
                '\n'.join(warnings) if warnings else False)

    def _compute_jv_revenue_count(self):
        for record in self:
            record.jv_revenue_count = self.env[
                'oil.jv.revenue'].search_count(
                [('royalty_id', '=', record.id)])

    def _compute_jv_bills(self):
        """Computes all vendor bills generated through the JV Revenue
        Distribution linked to this royalty (partner share bills +
        royalty bill)."""
        for record in self:
            revenues = self.env['oil.jv.revenue'].search(
                [('royalty_id', '=', record.id)])
            bill_ids = revenues.mapped('allocation_ids.bill_id')
            # Also include the royalty's own bill if it exists
            if record.bill_id and record.bill_id not in bill_ids:
                bill_ids |= record.bill_id
            record.jv_bill_ids = bill_ids
            record.jv_bill_count = len(bill_ids)

    def action_view_jv_bills(self):
        """Opens all vendor bills generated via JV Revenue Distribution."""
        self.ensure_one()
        bill_ids = self.jv_bill_ids.ids
        if not bill_ids:
            return
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Bills'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', bill_ids)],
            'target': 'current',
        }
        if len(bill_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = bill_ids[0]
        return action

    def action_view_jv_revenues(self):
        """Opens JV Revenue Distributions that imported from this royalty."""
        self.ensure_one()
        revenues = self.env['oil.jv.revenue'].search(
            [('royalty_id', '=', self.id)])
        action = {
            'type': 'ir.actions.act_window',
            'name': _('JV Revenue Distributions'),
            'res_model': 'oil.jv.revenue',
            'view_mode': 'list,form',
            'domain': [('id', 'in', revenues.ids)],
            'target': 'current',
        }
        if len(revenues) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = revenues[0].id
        return action

    def action_create_bill(self):
        """Override to prevent direct billing when a JV agreement is set.
        Royalties with a JV agreement must be billed through the
        Revenue Distribution flow to avoid double billing."""
        self.ensure_one()
        if self.jv_agreement_id:
            raise UserError(
                _("This royalty is linked to JV Agreement '%s'. "
                  "Please bill it through a Revenue Distribution instead "
                  "to avoid double billing.",
                  self.jv_agreement_id.name))
        return super().action_create_bill()

    def action_create_revenue_distribution(self):
        """Creates a JV Revenue Distribution from this confirmed royalty,
        pre-populating the revenue lines from royalty lines."""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(
                _("Only confirmed royalties can create revenue "
                  "distributions."))
        if not self.jv_agreement_id:
            raise UserError(
                _("Set a JV Agreement on this royalty before creating "
                  "a revenue distribution."))
        # Prevent duplicate revenue distributions for the same royalty
        existing = self.env['oil.jv.revenue'].search([
            ('royalty_id', '=', self.id),
        ], limit=1)
        if existing:
            raise UserError(
                _("A Revenue Distribution (%s) already exists for this "
                  "royalty. Please use the existing one.",
                  existing.name))

        revenue = self.env['oil.jv.revenue'].create({
            'agreement_id': self.jv_agreement_id.id,
            'royalty_id': self.id,
            'period_date': self.date,
        })
        # Import lines from this royalty
        revenue.action_import_from_royalty()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Revenue Distribution'),
            'res_model': 'oil.jv.revenue',
            'view_mode': 'form',
            'res_id': revenue.id,
            'target': 'current',
        }
