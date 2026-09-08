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


class ResPartner(models.Model):
    """Extends Partner with waste management contracts, billing rules, and SLA tracking."""
    _inherit = 'res.partner'

    generator_type = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('hospital', 'Hospital'),
        ('government', 'Government')
    ], string='Generator Type')

    regulatory_id = fields.Char(string='Regulatory ID', readonly=True)
    billing_mode = fields.Selection([
        ('consolidated', 'Consolidated Invoice'),
        ('monthly_run', 'Monthly Billing Run'),
    ], string='Billing Mode', default='consolidated', tracking=True,
       help="Determines which billing pipeline generates invoices for this customer.")
    contract_id = fields.One2many('wm.partner.contract', 'partner_id', string='Contract')
    collection_order_ids = fields.One2many(
        'wm.collection.order',
        'partner_id',
        string='Collection Orders'
    )
    is_contract_expiring = fields.Boolean(
        string='Is Contract Expiring',
        compute='_compute_contract_expiry_status'
    )
    is_contract_expired = fields.Boolean(
        string='Is Contract Expired',
        compute='_compute_contract_expiry_status'
    )
    collection_point_ids = fields.One2many(
        'wm.collection.point',
        'partner_id',
        string='Collection Points'
    )
    collection_point_count = fields.Integer(compute='_compute_collection_point_count')
    collection_order_count = fields.Integer(compute='_compute_collection_order_count')

    @api.depends('contract_id', 'collection_order_ids', 'generator_type')
    def _compute_is_generator(self):
        """
        Determine if the partner is a waste generator based on contracts, orders, or generator type.
        """
        for partner in self:
            partner.is_generator = bool(partner.contract_id or partner.collection_order_ids or partner.generator_type)

    # Compute, Inverse, and Search Methods
    @api.depends('contract_id', 'contract_id.to_date', 'contract_id.state')
    def _compute_contract_expiry_status(self):
        """
        Compute the contract expiration status for the partner.
        """
        today = fields.Date.today()
        for partner in self:
            if not partner.id or not isinstance(partner.id, int):
                partner.is_contract_expiring = False
                partner.is_contract_expired = False
                continue
            active_contract = self.env['wm.partner.contract'].search(
                [
                    ('partner_id', '=', partner.id),
                    ('state', '=', 'ongoing'),
                    ('to_date', '!=', False),
                ],
                limit=1
            )
            if active_contract and active_contract.to_date:
                days_left = (active_contract.to_date - today).days
                if days_left < 0:
                    partner.is_contract_expired = True
                    partner.is_contract_expiring = False
                elif 0 <= days_left < 15:
                    partner.is_contract_expired = False
                    partner.is_contract_expiring = True
                else:
                    partner.is_contract_expired = False
                    partner.is_contract_expiring = False
            else:
                partner.is_contract_expired = False
                partner.is_contract_expiring = False

    @api.depends('collection_point_ids')
    def _compute_collection_point_count(self):
        """
        Compute the total number of collection points associated with the
        partner.
        """
        for partner in self:
            partner.collection_point_count = len(partner.collection_point_ids)

    def _compute_collection_order_count(self):
        """
        Compute the total number of collection orders associated with the
        partner.
        """
        for partner in self:
            partner.collection_order_count = self.env['wm.collection.order'].search_count([('partner_id', '=', partner.id)])

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to assign a unique regulatory ID sequence to partners.
        """
        for vals in vals_list:
            if not vals.get('regulatory_id') or vals.get('regulatory_id') == 'New':
                vals['regulatory_id'] = self.env['ir.sequence'].next_by_code('res.partner') or 'New'
        return super().create(vals_list)

    def write(self, vals):
        """
        Override write to assign a unique regulatory ID sequence to partners if
        not already set.
        """
        res = super().write(vals)
        for partner in self:
            if not partner.regulatory_id or partner.regulatory_id == 'New':
                if not self.env.context.get('skip_regulatory_sequence'):
                    seq = self.env['ir.sequence'].next_by_code('res.partner') or 'New'
                    partner.with_context(skip_regulatory_sequence=True).write({'regulatory_id': seq})
        return res

    def action_view_collection_orders(self):
        """
        Return window action to view all collection orders linked to the
        partner.
        """
        self.ensure_one()
        return {
            'name': _('Collection Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'wm.collection.order',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_view_collection_points(self):
        """
        Return window action to view all collection points linked to the
        partner.
        """
        self.ensure_one()
        return {
            'name': _('Collection Points'),
            'type': 'ir.actions.act_window',
            'res_model': 'wm.collection.point',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
