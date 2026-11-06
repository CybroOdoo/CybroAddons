# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gee Paul Joby (odoo@cybrosys.com)
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
from odoo import api, models


class PosSession(models.Model):
    """
       Inherit pos session for adding multi barcode products in to session
    """
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config):
        """
        Extend POS data models loaded during POS initialization.

        This method adds the `multi.barcode.products` model to the list of
        models that are loaded into the Point of Sale frontend when a POS
        session is started.

        :param config: POS configuration record (pos.config)
        :return: List of model names to be loaded in POS
        :rtype: list
        """
        data = super()._load_pos_data_models(config)
        data += ['multi.barcode.products']
        return data
