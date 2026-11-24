# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class PetzenReview(models.Model):
    """Customer review submitted from the website and moderated in the backend."""
    _name = 'petzen.review'
    _description = 'Petzen Customer Review'
    _order = 'create_date desc'

    name = fields.Char(string='Reviewer Name', help='Name of the customer who wrote the review.', required=True)
    email = fields.Char(string='Email Address', help='Email address of the reviewer. It is never shown on the website.', required=True)
    rating = fields.Integer(string='Rating (1-5)', help='Rating given by the customer, from 1 to 5 stars.', default=5)
    review = fields.Text(string='Review Text', help='Text of the review written by the customer.', required=True)
    create_date = fields.Datetime(string='Submitted On', help='Date and time when the review was submitted.', readonly=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending', required=True, index=True,
        help="Only approved reviews are shown on the /reviews page.")

    _sql_constraints = [
        ('rating_range', 'CHECK(rating >= 1 AND rating <= 5)', 'The rating must be between 1 and 5.'),
    ]

    def action_approve(self):
        """Approve the selected reviews so they are shown on the website."""
        self.write({'state': 'approved'})

    def action_reject(self):
        """Reject the selected reviews so they stay hidden."""
        self.write({'state': 'rejected'})

    def action_reset_to_pending(self):
        """Move the selected reviews back to pending moderation."""
        self.write({'state': 'pending'})
