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

class OilAroPartnerShare(models.Model):
    """Model to track each JV partner's share of ARO costs per their Working Interest percentage."""
    _name = 'oil.aro.partner.share'
    _description = 'ARO Partner Cost Share'
    _order = 'working_interest desc'

    display_name = fields.Char(compute='_compute_display_name', help="A unique name or reference identifier used to track this record in the system.")

    def _compute_display_name(self):
        """Calculates and updates the 'name' value automatically based on related operational inputs."""
        for rec in self:
            rec.display_name = f"{rec.partner_id.name or ''} ({rec.working_interest}%)"

    obligation_id = fields.Many2one('oil.aro.obligation', string='ARO Obligation', ondelete='cascade', required=True, help="Link this transaction or record to the corresponding 'aro obligation' reference.")
    partner_id = fields.Many2one('res.partner', string='JV Partner', required=True, help="Link this transaction or record to the corresponding 'jv partner' reference.")
    working_interest = fields.Float(string='Working Interest (%)', digits=(6, 4), help="Specify the numerical measurement, volume, or financial amount for 'working interest (%)'.")
    currency_id = fields.Many2one(related='obligation_id.currency_id', readonly=True, help="Link this transaction or record to the corresponding 'currency id' reference.")
    share_amount = fields.Monetary(string='Share of Liability', currency_field='currency_id', compute='_compute_share_amount', store=True, help="The unit rate or total financial cost applied to this transaction.")

    @api.depends('obligation_id.current_liability_balance', 'working_interest')
    def _compute_share_amount(self):
        """Calculates and updates the 'amount' value automatically based on related operational inputs."""
        for rec in self:
            rec.share_amount = rec.obligation_id.current_liability_balance * (rec.working_interest / 100.0)
