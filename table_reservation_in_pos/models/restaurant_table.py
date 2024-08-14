# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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


class RestaurantTable(models.Model):
    """ The class RestaurantTable is used to add new fields in
     restaurant_table """
    _inherit = 'restaurant.table'

    reserved = fields.Boolean(string='Reserved', default=False,
                              help='Is Reserved or not')
    reservation_details = fields.Text(string='Reservation Details',
                                      help='View the reservation details')

    def reserve_table(self, details):
        """for reserve table with reservation details"""
        for table in self:
            table.reserved = True
            table.reservation_details = details

    def un_reserve_table(self):
        """for un reserve table"""
        for table in self:
            table.reserved = False
            table.reservation_details = ''
