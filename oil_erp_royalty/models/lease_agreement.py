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


class OilLeaseAgreement(models.Model):
    """
    Extends 'oil.lease.agreement' to link it with its associated royalties
    and provide tracking for royalty payments.
    """
    _inherit = 'oil.lease.agreement'

    royalty_ids = fields.One2many(
        'oil.royalty',
        'lease_id',
        string='Royalties',
        help="Royalty records linked to this lease agreement.")
    royalty_count = fields.Integer(
        string='Royalty Count',
        compute='_compute_royalty_count',
        help="Total number of royalty records for this lease.")

    def _compute_royalty_count(self):
        """
        Computes the total number of royalty records linked to this lease.
        """
        for record in self:
            record.royalty_count = len(record.royalty_ids)

    def action_view_royalties(self):
        """Open the royalties linked to this lease."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Royalties',
            'res_model': 'oil.royalty',
            'view_mode': 'list,form',
            'domain': [('lease_id', '=', self.id)],
            'context': {'default_lease_id': self.id},
        }
