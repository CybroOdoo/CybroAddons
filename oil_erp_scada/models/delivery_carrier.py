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

from odoo import fields, models


class DeliveryCarrierScada(models.Model):
    _inherit = 'delivery.carrier'

    scada_tag_ids = fields.One2many(
        'scada.tag',
        'carrier_id',
        string='SCADA Tags',
    )
    scada_tag_count = fields.Integer(
        compute='_compute_scada_tag_count',
        string='Tags',
    )

    def _compute_scada_tag_count(self):
        for rec in self:
            rec.scada_tag_count = len(rec.scada_tag_ids)

    def action_view_scada_tags(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'SCADA Tags — {self.name}',
            'res_model': 'scada.tag',
            'view_mode': 'list,form',
            'domain': [('carrier_id', '=', self.id)],
            'context': {
                'default_carrier_id': self.id,
                'default_odoo_model': 'delivery.carrier',
                'default_measure_flow_rate': True,
            },
        }

    def action_view_readings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Readings — {self.name}',
            'res_model': 'scada.reading',
            'view_mode': 'list,graph',
            'domain': [('tag_id', 'in', self.scada_tag_ids.ids)],
        }
