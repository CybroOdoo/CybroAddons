#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import date
from odoo import api, fields, models


class SalonChair(models.Model):
    """Class to create 'salon.chair' to manage chairs in salon"""
    _name = 'salon.chair'
    _description = 'Salon Chair'

    name = fields.Char(string="Chair", required=True, readonly=True,
                       default="New", help="Name for chair")
    number_of_orders = fields.Integer(string="No.of Orders", help="Number of active orders on the chair")
    collection_today = fields.Float(string="Today's Collection",
                                    help="Today's collection")
    user_id = fields.Many2one(
        'res.users', readonly=True,
        help="You can select the user from the Users tab. "
             "The last user from the Users Tab will be selected "
             "as the Current User.")
    date = fields.Datetime(help="Chair available date", required=True)
    user_line = fields.One2many('salon.chair.user', 'salon_chair_id',
                                string="Users", help="Salon chair users")
    total_time_taken_chair = fields.Float(string="Time Reserved(Hrs)",
                                          help="Reserved time")
    active_booking_chairs = fields.Boolean(help="Check to make the chair available for online booking")
    chair_created_user = fields.Integer(string="Salon Chair Created User",
                                        default=lambda self: self.env.uid,
                                        help="Chair created user")

    @api.model_create_multi
    def create(self, values):
        """Add sequence for chair, start date and end date on creating record"""
        for vals in values:
            if vals.get('name', self.env._('New')) == self.env._('New'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('salon_chair_sequence')
                    or self.env._('New')
                )
            if values and 'user_line' in values[0].keys():
                if vals.get('user_line'):
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
        return super(SalonChair, self).create(values)

    def collection_today_updater(self):
        """ Function to update the collection on the day for each chair """
        get_stage = self.env['salon.stage']._get_stage_id
        invoiced_stages = [
            s for s in [get_stage('invoiced'), get_stage('closed')] if s]
        for chair in self.browse(self._search([])):
            invoiced_records = self.env['salon.order'].search(
                [('stage_id', 'in', invoiced_stages),
                 ('chair_id', '=', chair.id)])
            total = 0
            for rows in invoiced_records:
                invoiced_date = str(rows.date)[:10]
                if invoiced_date == str(date.today()):
                    total = total + rows.price_subtotal
            chair.collection_today = total
