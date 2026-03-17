# -- coding: utf-8 --
#############################################################################
#
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


class ResPartner(models.Model):
    """Extend res.partner with a churn score smart button."""

    _inherit = 'res.partner'

    # ------------------------------------------------------------------
    # Churn score link
    # ------------------------------------------------------------------
    churn_score_id = fields.One2many(
        'churn.score',
        'partner_id',
        string='Churn Scores',
    )
    churn_score_value = fields.Float(
        string='Churn Score',
        compute='_compute_churn_score_data',
        store=False,
    )
    churn_risk_level = fields.Selection(
        selection=[
            ('low',      'Low'),
            ('medium',   'Medium'),
            ('high',     'High'),
            ('critical', 'Critical'),
        ],
        string='Churn Risk',
        compute='_compute_churn_score_data',
        store=False,
    )
    churn_score_count = fields.Integer(
        string='Churn Records',
        compute='_compute_churn_score_data',
        store=False,
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends('churn_score_id', 'churn_score_id.churn_score',
                 'churn_score_id.risk_level')
    def _compute_churn_score_data(self):
        for partner in self:
            score_rec = partner.churn_score_id[:1]
            partner.churn_score_count = len(partner.churn_score_id)
            if score_rec:
                partner.churn_score_value = score_rec.churn_score
                partner.churn_risk_level  = score_rec.risk_level
            else:
                partner.churn_score_value = 0.0
                partner.churn_risk_level  = False

    # ------------------------------------------------------------------
    # Smart button action
    # ------------------------------------------------------------------
    def action_open_churn_score(self):
        """Open the churn score form (or list if multiple records exist)."""
        self.ensure_one()
        score_recs = self.churn_score_id

        if not score_recs:
            # Auto-create and compute on the fly
            new_rec = self.env['churn.score'].create({'partner_id': self.id})
            new_rec.action_compute_score()
            score_recs = new_rec

        if len(score_recs) == 1:
            return {
                'type':      'ir.actions.act_window',
                'res_model': 'churn.score',
                'res_id':    score_recs.id,
                'view_mode': 'form',
                'target':    'current',
            }
        return {
            'type':      'ir.actions.act_window',
            'res_model': 'churn.score',
            'view_mode': 'list,form',
            'domain':    [('partner_id', '=', self.id)],
            'target':    'current',
        }
