# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models


class PosSession(models.Model):
    """Inherit the pos_session model to load the WhatsApp number field into
    the POS session."""
    _inherit = 'pos.session'

    def _loader_params_res_partner(self):
        """Extends the loader parameters for the res_partner model to include
        the 'whatsapp_number' field."""
        result = super()._loader_params_res_partner()
        result['search_params']['fields'].extend(['whatsapp_number'])
        return result

    def _loader_params_res_users(self):
        """Extends the loader parameters for the res_users model to include
        the 'whatsapp_groups_checks' field."""
        result = super()._loader_params_res_users()
        result['search_params']['fields'].extend(['whatsapp_groups_checks'])
        return result
