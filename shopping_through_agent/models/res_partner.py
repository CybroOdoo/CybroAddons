# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class ResPartner(models.Model):
    """Class to add the fields in partner form"""
    _inherit = 'res.partner'

    agent_id = fields.Many2one(comodel_name='res.partner', string='Agent',
                               help='Select an agent for the customer to '
                                    'allow agent can create sale order for '
                                    'the customer')
    is_agent = fields.Boolean(string='Is Agent',
                              help='Enable if this person is a agent')

    @api.onchange('is_agent')
    def _onchange_agent(self):
        """On change function for the agent field"""
        if not self.is_agent:
            self.agent_id = ''
            self.search([('agent_id', '=', self.name)]).write({'agent_id': ''})
