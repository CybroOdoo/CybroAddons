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


class SaleOrder(models.Model):
    """Extends Sale Order with waste management service contract conversion actions."""
    _inherit = 'sale.order'

    wm_contract_ids = fields.One2many(
        'wm.partner.contract',
        'sale_order_id',
        string='Waste Contracts',
        readonly=True,
    )
    wm_contract_count = fields.Integer(
        string='Contracts',
        compute='_compute_wm_contract_count',
    )

    @api.depends('wm_contract_ids')
    def _compute_wm_contract_count(self):
        """
        Compute the total number of associated wm contract records linked to
        this SaleOrder to update smart buttons and summary badges.
        """
        for order in self:
            order.wm_contract_count = len(order.wm_contract_ids)

    def _action_confirm(self):
        """
        On confirmation, if this quotation originated from a WM
        opportunity with waste category lines, schedule an activity         on
        the lead for contract creation.
        """
        result = super()._action_confirm()
        for order in self:
            lead = order.opportunity_id
            if lead and lead.lead_line_ids and not lead.wm_contract_ids:
                lead.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Quotation accepted — create the waste management contract'),
                    user_id=lead.user_id.id or self.env.uid,
                )
        return result

    def action_convert_to_wm_contract(self):
        """
        Convert a confirmed sale order for waste management services into a
        wm.partner.contract record, pre-populating contract terms from the sale
        order lines.
        """
        self.ensure_one()
        lead = self.opportunity_id
        existing = self.env['wm.partner.contract'].search([
            ('partner_id', '=', self.partner_id.id),
            ('state', 'in', ('sent', 'signed', 'confirmed', 'ongoing')),
        ], limit=1)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Convert Quotation to Contract'),
            'res_model': 'wm.lead.conversion.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_lead_id': lead.id if lead else False,
                'default_partner_id': self.partner_id.id,
                'default_frequency': lead.wm_frequency or 'weekly' if lead else 'weekly',
                'default_service_type': lead.wm_service_type or 'collection' if lead else 'collection',
                'default_fixed_price': self.amount_total,
                'default_has_existing_contract': bool(existing),
                'default_existing_contract_name': existing.name if existing else '',
            },
        }

    def action_view_wm_contracts(self):
        """
        Smart button: view all contracts linked to this sale order.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contracts'),
            'res_model': 'wm.partner.contract',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_partner_id': self.partner_id.id, 'default_sale_order_id': self.id},
        }
