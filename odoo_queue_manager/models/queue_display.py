# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class QueueDisplay(models.Model):
    """Model representing a queue display"""
    _name = 'queue.display'
    _description = 'Queue Display'

    name = fields.Char(string='Display Name', required=True)
    counter_id = fields.Many2one(
        'queue.counter',
        string='Counter',
        required=True
    )
    current_token = fields.Char(
        string='Current Token',
        compute='_compute_current_token'
    )
    display_url = fields.Char(
        string='Display Link',
        compute='_compute_display_url',
        store=True
    )

    @api.depends('counter_id')
    def _compute_display_url(self):
        """Function to compute display url"""
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url'
        )
        for rec in self:
            if rec.counter_id:
                rec.display_url = (
                    f"{base_url}/queue/display/{rec.counter_id.id}"
                )
            else:
                rec.display_url = False

    def _compute_current_token(self):
        """Function to compute current token"""
        for rec in self:
            token = self.env['token.token'].sudo().search([
                ('counter_id', '=', rec.counter_id.id),
                ('state', '=', 'in_progress')
            ], limit=1)

            rec.current_token = token.token if token else "No Token"
