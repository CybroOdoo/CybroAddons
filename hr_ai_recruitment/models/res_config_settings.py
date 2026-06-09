# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreerag PM (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    """
    Extends system settings to include AI shortlisting configuration.
    Allows administrators to enable or disable AI-based applicant shortlisting
    globally through the settings interface.
    """
    _inherit = 'res.config.settings'

    is_ai_shortlist = fields.Boolean(
        string='Enable AI Shortlisting',
        config_parameter='hr_ai_recruitment.is_ai_shortlist',
        help="Enable this option to allow AI-powered applicant shortlisting "
             "in the recruitment process."
    )

    @api.model
    def set_values(self):
        """Override set_values to update menu visibility dynamically."""
        super(ResConfigSettings, self).set_values()
        ir_menu = self.env.ref('hr_ai_recruitment.hr_shortlist_menu',
                               raise_if_not_found=False)
        if ir_menu:
            is_enabled = self.env['ir.config_parameter'].sudo().get_param(
                'hr_ai_recruitment.is_ai_shortlist', 'False') == 'True'
            ir_menu.sudo().write({'active': is_enabled})
