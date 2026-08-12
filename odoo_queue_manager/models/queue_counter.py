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
from odoo import fields, models


class TokenInterface(models.Model):
    """Model representing a token interface"""
    _name = 'queue.counter'

    name = fields.Char(string="Counter Name", required=True, help="Shows the counter name")

    def action_start_process(self):
        """ Function to get the select department wizard"""
        return {
            'name': 'Start Processing',
            'type': 'ir.actions.act_window',
            'res_model': 'select.department',
            'view_mode': 'form',
            'context': {
                'default_counter_id': self.id},
            'target': 'new'
        }
