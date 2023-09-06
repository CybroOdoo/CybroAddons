# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Risvana AR (odoo@cybrosys.com)
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
from odoo import fields, models, tools


class VenueBookingReport(models.Model):
    _name = "venue.booking.report"
    _description = "Venue Booking Analysis Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    name = fields.Char('Booking Reference', readonly=True,
                       help="Booking Reference field for the Reporting")
    date = fields.Datetime('Booking Date', readonly=True,
                           help="Booking Date field for the Reporting")
    partner_id = fields.Many2one('res.partner',
                                 'Customer', readonly=True,
                                 help="Partner ID field for the Reporting")
    total = fields.Float('Total', readonly=True,
                         help="Total amount for the Booking Values")
    state = fields.Selection([
        ('draft', 'Enquiry'),
        ('confirm', 'Confirmed'),
        ('invoice', 'Invoiced'),
        ('close', 'Closed'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, help="The selection field for the Booking")

    def init(self):
        """Initialize the function to get the Booking Details"""
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
        CREATE OR REPLACE VIEW %s AS (
            SELECT
                vb.id as id,
                vb.name as name,
                vb.date as date,
                vb.partner_id as partner_id,
                vb.total as total,
                vb.state as state
            FROM venue_booking vb
            WHERE vb.state IN ('confirm', 'invoice')
            GROUP BY
                vb.id,
                vb.name,
                vb.date,
                vb.partner_id,
                vb.total,
                vb.state
            ORDER BY vb.id
        )
    """ % (self._table,))


