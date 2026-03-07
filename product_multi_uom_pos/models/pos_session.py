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
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        """Updating pos data models to include pos.multi.uom."""
        data = super()._load_pos_data_models(config_id)
        data.append('pos.multi.uom')
        return data

    def _load_pos_data_pos_multi_uom(self, data):
        """Loading data for pos.multi.uom."""
        records = self.env['pos.multi.uom'].search_read(domain=[], fields=['product_template_id', 'uom_id', 'price'])

        result = {}
        for rec in records:
            tid = rec['product_template_id'][0] if isinstance(rec['product_template_id'], tuple) else rec[
                'product_template_id']
            result.setdefault(tid, []).append(rec)
        return result
