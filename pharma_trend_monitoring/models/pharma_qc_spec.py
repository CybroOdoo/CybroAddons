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
from odoo import models

from .pharma_trend_parameter import parameter_key


class PharmaQcSpec(models.Model):
    """Starts or updates trend histories when a specification is approved."""
    _inherit = 'pharma.qc.spec'

    def action_approve(self):
        """Approve, then link watched parameters to this specification version."""
        res = super().action_approve()
        Parameter = self.env['pharma.trend.parameter'].sudo()
        for spec in self:
            for line in spec.parameter_ids:
                existing = Parameter.search([
                    ('product_id', '=', spec.product_id.id),
                    ('stage', '=', spec.stage),
                    ('parameter_key', '=', parameter_key(line.parameter_name)),
                ])
                existing._pharma_sync_spec_line(line)
                if line.is_trended and not existing.filtered(
                        lambda p: p.company_id == self.env.company):
                    Parameter._pharma_get_or_create(line, self.env.company)
            # A parameter dropped from the new version is no longer watched.
            keys = [parameter_key(line.parameter_name) for line in spec.parameter_ids]
            Parameter.search([
                ('product_id', '=', spec.product_id.id),
                ('stage', '=', spec.stage),
                ('parameter_key', 'not in', keys),
                ('is_trended', '=', True),
            ]).write({'is_trended': False})
        return res
