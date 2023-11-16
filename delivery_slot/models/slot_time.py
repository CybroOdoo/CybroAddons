# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Muhsina V (odoo@cybrosys.com)
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
from odoo import fields, models


class SlotTime(models.Model):
    """Slot time model"""
    _name = 'slot.time'
    _description = 'Delivery time'

    name = fields.Char(string='Slot', help="Slot name")
    slot_type = fields.Selection([
        ('home', 'Home Hours'), ('office', 'Office Hours')],
        string="Slot type", help="Slot will be shown based on this slot type")
    time_from = fields.Selection([
        ('0', '12:00 AM'), ('1', '1:00 AM'),
        ('2', '2:00 AM'), ('3', '3:00 AM'),
        ('4', '4:00 AM'), ('5', '5:00 AM'),
        ('6', '6:00 AM'), ('7', '7:00 AM'),
        ('8', '8:00 AM'), ('9', '9:00 AM'),
        ('10', '10:00 AM'), ('11', '11:00 AM'),
        ('12', '12:00 PM'), ('13', '1:00 PM'),
        ('14', '2:00 PM'), ('15', '3:00 PM'),
        ('16', '4:00 PM'), ('17', '5:00 PM'),
        ('18', '6:00 PM'), ('19', '7:00 PM'),
        ('20', '8:00 PM'), ('21', '9:00 PM'),
        ('22', '10:00 PM'), ('23', '11:00 PM')
    ], string='Time From', help="From time")
    time_to = fields.Selection([
        ('0', '12:00 AM'), ('1', '1:00 AM'),
        ('2', '2:00 AM'), ('3', '3:00 AM'),
        ('4', '4:00 AM'), ('5', '5:00 AM'),
        ('6', '6:00 AM'), ('7', '7:00 AM'),
        ('8', '8:00 AM'), ('9', '9:00 AM'),
        ('10', '10:00 AM'), ('11', '11:00 AM'),
        ('12', '12:00 PM'), ('13', '1:00 PM'),
        ('14', '2:00 PM'), ('15', '3:00 PM'),
        ('16', '4:00 PM'), ('17', '5:00 PM'),
        ('18', '6:00 PM'), ('19', '7:00 PM'),
        ('20', '8:00 PM'), ('21', '9:00 PM'),
        ('22', '10:00 PM'), ('23', '11:00 PM')],
        string='Time To', help="To time")
