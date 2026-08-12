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

from odoo import api, fields, models
from odoo.tools.translate import _

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    is_decommissioned = fields.Boolean(string='Decommissioned / End of Life', default=False, tracking=True,
                                      help="Flag this asset as scrapped or at its end of life to suggest ARO creation.")
    is_oil_equipment = fields.Boolean(string='Oil & Gas Equipment', default=False, tracking=True,
                                     help="Marks this as an Oil & Gas field asset subject to ARO certification monitoring.")
    certification_expiry = fields.Date(string='Certification Expiry Date', tracking=True,
                                       help="Operating certification / inspection expiry date. Triggers ARO suggestion when expired.")
    aro_obligation_ids = fields.One2many('oil.aro.obligation', 'equipment_id', string='ARO Obligations', help="Link this transaction or record to the corresponding 'aro obligations' reference.")
    aro_count = fields.Integer(compute='_compute_aro_count', string='ARO Count', help="Specify the numerical measurement, volume, or financial amount for 'aro count'.")

    @api.depends('aro_obligation_ids')
    def _compute_aro_count(self):
        """Calculates and updates the 'count' value automatically based on related operational inputs."""
        for rec in self:
            rec.aro_count = len(rec.aro_obligation_ids)

    @api.depends('purchase_cost', 'purchase_date', 'useful_life_years', 'aro_obligation_ids.initial_pv', 'aro_obligation_ids.state')
    def _compute_current_book_value(self):
        """Calculates and updates the 'book value' value automatically based on related operational inputs."""
        today = fields.Date.today()
        for rec in self:
            active_aro = rec.aro_obligation_ids.filtered(lambda a: a.state not in ('draft', 'cancelled'))
            aro_capitalized = sum(active_aro.mapped('initial_pv'))
            total_depreciable_cost = (rec.purchase_cost or 0.0) + aro_capitalized

            if not total_depreciable_cost:
                rec.current_book_value = 0.0
                rec.annual_depreciation = 0.0
                continue
            if not rec.purchase_date or not rec.useful_life_years:
                rec.current_book_value = total_depreciable_cost
                rec.annual_depreciation = total_depreciable_cost / rec.useful_life_years if rec.useful_life_years else 0.0
                continue
            elapsed_days = max((today - rec.purchase_date).days, 0)
            useful_days = max(int(rec.useful_life_years * 365), 1)
            depreciation = total_depreciable_cost * min(elapsed_days / useful_days, 1.0)
            rec.current_book_value = max(total_depreciable_cost - depreciation, 0.0)
            rec.annual_depreciation = total_depreciable_cost / rec.useful_life_years if rec.useful_life_years else 0.0

    def write(self, vals):
        """Updates the current record's details, performing sanity checks on the modified fields."""
        res = super(MaintenanceEquipment, self).write(vals)
        if 'is_decommissioned' in vals and vals['is_decommissioned']:
            for rec in self:
                # Suggest creating ARO if not already created
                existing = self.env['oil.aro.obligation'].search([
                    ('equipment_id', '=', rec.id),
                    ('state', '!=', 'cancelled')
                ])
                if not existing:
                    self.env['oil.aro.obligation'].create({
                        'name': _("ARO Suggestion: %s") % rec.name,
                        'asset_kind': 'equipment',
                        'equipment_id': rec.id,
                        'state': 'draft',
                        'future_cost': 10000.0,
                        'description': _("Automated ARO suggestion triggered by decommissioning / end-of-life status on equipment: %s") % rec.name,
                    })
                    rec.message_post(body=_("Equipment marked as decommissioned. Suggestion for ARO Obligation created."))
        return res

    def action_view_aro(self):
        """Triggers the transition of the record to proceed with the 'view aro' step in the workflow."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'ARO Obligations',
            'res_model': 'oil.aro.obligation',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {
                'default_equipment_id': self.id,
                'default_asset_kind': 'equipment',
            },
        }
