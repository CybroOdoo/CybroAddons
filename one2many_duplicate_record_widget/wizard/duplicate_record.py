# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
import logging
from odoo import models, api
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class DuplicateRecord(models.TransientModel):
    """Created model to duplicate the record"""
    _name = 'duplicate.record'
    _description = 'Duplicate Records'

    @api.model
    def action_duplicate_records(self, selected_values):
        """Duplicating the records.
              params: dict selected_values: list of records of selected
              One2many fields"""
        record = self.env[selected_values.get('model')]. \
            browse(selected_values.get('values'))
        try:
            for rec in record:
                datas = list(rec.read())
                for data in datas[0]:
                    is_tuple = type(datas[0][data]) is tuple
                    if is_tuple:
                        datas[0][data] = datas[0][data][0]
                self.env[selected_values['model']].create(datas)
        except UserError as e:
            _logger.info(e)
        return True
