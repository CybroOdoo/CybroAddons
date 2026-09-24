# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited res.config.settings to add salesperson follower restriction
    toggle."""
    _inherit = 'res.config.settings'

    enable_salesperson_follower_restriction = fields.Boolean(
        string='Salesperson Follower Restriction',
        help='When enabled, if the assigned Salesperson and the Sales Order '
             'creator are different users, the Salesperson will be removed '
             'from the follower list of the invoice created from the '
             'Sales Order.',
        config_parameter='invoice_salesperson_follower_restriction.enable_restriction',
    )
