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
from odoo import api, models
from odoo.exceptions import ValidationError


class PharmaQcTestOrder(models.Model):
    """Instrument defaults on generated lines, and the approval backstop."""
    _inherit = 'pharma.qc.test.order'

    @api.onchange('spec_id')
    def _onchange_spec_id(self):
        """Propose each parameter's default instrument on the generated lines."""
        res = super()._onchange_spec_id()
        for line in self.result_line_ids:
            if not line.instrument_id and line.parameter_id.default_instrument_id:
                line.instrument_id = line.parameter_id.default_instrument_id
        return res

    def action_approve(self):
        """Refuse approval of a result measured out of calibration."""
        mode = self.env['maintenance.equipment']._pharma_equipment_settings()['check']
        if mode == 'block':
            for order in self:
                bad = order.result_line_ids.filtered(
                    lambda line: line.instrument_id and not line.instrument_calibration_ok)
                if bad:
                    raise ValidationError(self.env._(
                        'Test order %(order)s cannot be approved: %(params)s '
                        'were measured on an instrument out of calibration.',
                        order=order.name,
                        params=', '.join(bad.mapped('parameter') or ['?'])))
        return super().action_approve()
