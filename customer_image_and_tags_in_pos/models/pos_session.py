# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models, api


class PosSession(models.Model):
    """ Inherit pos session for load fields from res partner model"""
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        """Add  the  res partner category models into the pos session."""
        data = super()._load_pos_data_models(config_id)
        data += ['res.partner.category']
        return data
