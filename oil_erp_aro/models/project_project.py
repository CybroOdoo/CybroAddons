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

class ProjectProject(models.Model):
    """Extend project.project to optionally link to an ARO obligation."""
    _inherit = 'project.project'

    aro_obligation_id = fields.Many2one('oil.aro.obligation', string='ARO Obligation',
                                        help='If this project relates to a decommissioning, link the ARO here.')
    aro_liability_balance = fields.Monetary(related='aro_obligation_id.current_liability_balance',
                                            string='ARO Liability', readonly=True, help="Specify the numerical measurement, volume, or financial amount for 'aro liability'.")
    aro_wip_total = fields.Monetary(related='aro_obligation_id.wip_total', string='Total WIP', readonly=True, help="Specify the numerical measurement, volume, or financial amount for 'total wip'.")
    aro_state = fields.Selection(related='aro_obligation_id.state', string='ARO Status', readonly=True, help="The current step of this record in its operational or approval lifecycle.")
