# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Renu M (odoo@cybrosys.info)
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
from odoo import api, fields, models, tools
from odoo.tools import format_datetime


class EventEvent(models.Model):
    _inherit = 'event.event'

    date_begin_pred_located = fields.Char(
        compute='_compute_date_begin_pred_located',
        store=True,
    )

    @api.depends('date_begin', 'date_tz')
    def _compute_date_begin_pred_located(self):
        for record in self:
            record.date_begin_pred_located = format_datetime(
                self.env,
                record.date_begin,
                tz=record.date_tz,
                dt_format='medium')
