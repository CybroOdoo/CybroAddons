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


class ProjectProjectScada(models.Model):
    """
    Extends project.project with SCADA integration fields for live
    downhole telemetry: reservoir pressure, GOR, water cut, etc.
    """
    _inherit = 'project.project'

    scada_tag_ids = fields.One2many(
        'scada.tag',
        'project_id',
        string='SCADA Tags',
    )
    scada_tag_count = fields.Integer(
        compute='_compute_scada_tag_count',
        string='Tags',
    )
    last_scada_sync = fields.Datetime(
        string='Last SCADA Sync',
        readonly=True,
    )
    live_reservoir_pressure = fields.Float(
        string='Live Reservoir Pressure (PSI)',
        readonly=True,
        help='Latest downhole pressure reading pushed from SCADA.',
    )
    live_gor = fields.Float(
        string='Live GOR (scf/bbl)',
        readonly=True,
        help='Latest Gas-Oil Ratio pushed from SCADA.',
    )
    live_water_cut = fields.Float(
        string='Live Water Cut (%)',
        readonly=True,
        help='Latest water cut percentage pushed from SCADA.',
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
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'default_odoo_model': 'project.project',
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
