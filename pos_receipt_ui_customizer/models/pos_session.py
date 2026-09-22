# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.info)
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
        Extend POS Session to load custom receipt configuration
        in the POS frontend.
        """
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """
        Ensure the 'pos.receipt' model is loaded in the POS frontend."""
        res = super()._pos_ui_models_to_load()
        if 'pos.receipt' not in res:
            res.append('pos.receipt')
        return res


    def _loader_params_pos_receipt(self):
        """
               Specify the receipt and QR-related fields
               that should be available in the POS UI.
        """
        return {
            'search_params': {
                'fields': ['id', 'design_receipt', 'design_receipt_font_style', 'qr_size', 'qr_position',
                           'receipt_qr_size', 'receipt_qr_position', 'enable_qr', 'enable_qr_section'],
            }
        }