# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjali VP (Contact : odoo@cybrosys.com)
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
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)

class PosConfig(models.Model):
    """Inherits 'pos.config' and adds new field"""
    _inherit = "pos.config"

    pos_multi_uom = fields.Boolean(
        string="Multi UoM",
        help="Enable the option change UoM of products in POS"
    )

    def read(self, fields=None, load='_classic_read'):
        """Overriding read function to include the fields when
        fetching the pos.config records."""
        return super().read(fields, load)
