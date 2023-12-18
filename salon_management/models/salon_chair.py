# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from datetime import date
from odoo import api, fields, models, _


class SalonChair(models.Model):
    """Class to create 'salon.chair' to manage chairs in salon"""
    _name = 'salon.chair'
    _description = 'Salon Chair'

    name = fields.Char(string="Chair", required=True, readonly=True,
                       default="New", help="Name for chair")
    number_of_orders = fields.Integer(string="No.of Orders", help="Number of ")
    collection_today = fields.Float(string="Today's Collection", 
                                    help="Today's collection")
    user_id = fields.Many2one(
        'res.users', string="User", readonly=True,
        help="You can select the user from the Users Tab"
             "Last user from the Users Tab will be selected "
             "as the Current User.")
    date = fields.Datetime(string="Date", help="Chair available date")
    user_line = fields.One2many('salon.chair.user', 'salon_chair_id',
                                string="Users", help="Salon chair users")
    total_time_taken_chair = fields.Float(string="Time Reserved(Hrs)",
                                          help="Reserved time")
    active_booking_chairs = fields.Boolean(string="Active booking chairs",
                                           help="Check is chair a active chair")
    chair_created_user = fields.Integer(string="Salon Chair Created User",
                                        default=lambda self: self._uid,
                                        help="Chair created user")

    @api.model_create_multi
    def create(self, values):
        """Add sequence for chair, start date and end date on creating record"""
        for vals in values:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'salon_chair_sequence')
            if 'user_line' in values[0].keys():
                if vals['user_line']:
                    date_changer = []
                    for elements in vals['user_line']:
                        date_changer.append(elements[2]['start_date'])
                    number = 0
                    for elements in vals['user_line']:
                        number += 1
                        if len(vals['user_line']) == number:
                            break
                        elements[2]['end_date'] = date_changer[number]
                    vals['user_id'] = vals['user_line'][len(
                        (vals['user_line'])) - 1][2]['user_id']
                    vals['date'] = vals['user_line'][len(
                        (vals['user_line'])) - 1][2]['start_date']
            return super(SalonChair, self).create(vals)

    def collection_today_updater(self):
        """ Function to update the collection on the day for each chair """
        salon_chair = self.env['salon.chair']
        for values in self.search([]):
            chair_obj = salon_chair.browse(values.ids)
            invoiced_records = chair_obj.env['salon.order'].search(
                [('stage_id', 'in', [3, 4]), ('chair_id', '=', chair_obj.id)])
            total = 0
            for rows in invoiced_records:
                invoiced_date = str(rows.date)
                invoiced_date = invoiced_date[0:10]
                if invoiced_date == str(date.today()):
                    total = total + rows.price_subtotal
            chair_obj.collection_today = total
