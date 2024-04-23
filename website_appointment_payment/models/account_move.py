# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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


class AccountMove(models.Model):
    """When an invoice is paid,an event is created to corresponding booking"""
    _inherit = "account.move"

    calendar_booking_ids = fields.One2many("appointment.booking",
                                           "account_move_id",
                                           string="Meeting Booking",
                                           help="shows the appointment "
                                                "booking related to the "
                                                "invoice")

    def _invoice_paid_hook(self):
        """when invoice is paid, create event from calendar booking"""
        res = super()._invoice_paid_hook()
        self.calendar_booking_ids.make_event()
        return res
