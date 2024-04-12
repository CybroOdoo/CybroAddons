# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class WebsiteEstimatedDeliveryTime(models.Model):
    """This is for adding the estimated delivery time for all product"""
    _name = 'website.estimated.delivery.time'
    _description = "Estimated Delivery Time"

    available_message = fields.Char(
        string="Message To Display When The Product Is Available",
        help="Message to display when the product is available", required=True,
        default="This Product Will Be Delivered Within")
    unavailable_message = fields.Char(
        string="Message To Display When The Product Is Unavailable",
        help="Message to display when the product is unavailable",
        required=True, default="This Product Is Not Available In Your Location")
    display_mode = fields.Selection([('exact', 'Exact'),
                                     ('range', 'Range')],
                                    string='Display Mode', default='exact',
                                    required=True)
    delivery_day_range = fields.Selection([
        ('days_before', 'Add Days Before'),
        ('days_after', 'Add Days After')],
        string='Delivery Day Range',
        default='days_after', required=True,
        help="Day range to deliver products")
    number_of_days = fields.Integer(string="Number Of Days",
                                    help="The number of days added or "
                                         "subtracted the actual days in order"
                                         "to create delivery range",
                                    required=True)
    estimated_delivery_time_ids = fields.One2many(
        'estimated.delivery.time',
        'website_estimated_delivery_time_id',
        required=True,
        string="Estimated Delivery Time",
        help="Add Estimated delivery Time")

    def action_website_estimated_delivery_time(self):
        """This is for deleting the previous records in the
        website.estimated.delivery.time and estimated.delivery.time"""
        for rec in self.env['website.estimated.delivery.time'].search(
                [('id', '!=', self.id)]):
            rec.unlink()
        for records in self.env['estimated.delivery.time'].search(
                [('id', '!=', self.estimated_delivery_time_ids.ids)]):
            records.unlink()
