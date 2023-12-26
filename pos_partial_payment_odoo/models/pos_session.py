# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
from odoo import models


class PosSession(models.Model):
    """
    This class extends the 'pos.session' model to add functionality related to loading
    parameters of the 'res.partner' model within the session
    """
    _inherit = 'pos.session'

    def _loader_params_res_partner(self):
        """
        This function loads the parameters of res.partner in the session.
        ----------------------------------------
        @param self: object pointer
        @return result: params of res.partner model
        """
        result = super(PosSession, self)._loader_params_res_partner()
        result['search_params']['fields'].append('prevent_partial_payment')
        return result
