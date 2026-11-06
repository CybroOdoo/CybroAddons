# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>)
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
################################################################################
from odoo import api, fields, models


class PosButtons(models.Model):
    """This is used to store the button"""
    _name = 'pos.buttons'
    _description = "POS Buttons"

    name = fields.Char(
        string="Name",
        help=(
            "Technical name of the POS button available for "
            "user-based visibility rules."
        ),
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Loading fields"""
        return ['id', 'name']

    @api.model
    def _load_pos_data_domain(self, data):
        """Loading domain"""
        return []

    def _load_pos_data(self, data):
        """Loading data"""
        domain = self._load_pos_data_domain(data)
        fields = self._load_pos_data_fields(data['pos.config']['data'][0]['id'])
        return {
            'data': self.search_read(domain, fields,
                                     load=False) if domain is not False else [],
            'fields': fields,
        }
