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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Lists the Preventive Action add-on among the premium features."""
    _inherit = 'res.config.settings'

    module_pharma_capa_preventive = fields.Boolean(
        string='Preventive Action',
        help='Installs the paid Preventive Action add-on.',
    )
    pharma_capa_preventive_found = fields.Boolean(
        compute='_compute_pharma_premium_found',
        help='True when the Preventive Action module is available on this server.',
    )

    def _compute_pharma_premium_found(self):
        """Offer the Preventive Action toggle only once its module is on the server."""
        super()._compute_pharma_premium_found()
        found = self.env['pharma.premium.feature']._pharma_feature_on_server('capa_preventive')
        for rec in self:
            rec.pharma_capa_preventive_found = found
