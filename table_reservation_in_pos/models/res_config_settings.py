# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Abbas(odoo@cybrosys.com)
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
from odoo import fields, models


class PosSettings(models.TransientModel):
    """ The class PosSettings is used to add new field in
             res.config.settings """
    _inherit = 'res.config.settings'

    table_reservation = fields.Boolean(string="Table Reservation",
                                        related=
                                        'pos_config_id.table_reservation',
                                        readonly=False,
                                        help='Enable reservation'
                                             ' for adding reservation',
                                        config_parameter=
                                        'table_reservation_in_pos.'
                                        'table_reservation')
