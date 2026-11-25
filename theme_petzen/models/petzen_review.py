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
    """Customer review submitted from the website /reviews page; it is shown on
    the page once approved from Website > Configuration > Customer Reviews."""
    _name = 'petzen.review'
    _description = 'Petzen Customer Review'
    _order = 'create_date desc'

    name = fields.Char(
        string='Reviewer Name', required=True,
        help="Name of the customer, shown on the /reviews page.")
    email = fields.Char(
        string='Email Address', required=True,
        help="Email of the customer, never shown on the website.")
    rating = fields.Integer(
        string='Rating (1-5)', default=5,
        help="Number of stars given by the customer, from 1 to 5.")
    review = fields.Text(string='Review Text', required=True,
                         help="Review written by the customer.")
    customer_type = fields.Selection([
        ('verified', 'Verified Customer'),
        ('dog_owner', 'Dog Owner'),
        ('cat_owner', 'Cat Owner'),
        ('bird_lover', 'Bird Lover'),
        ('fish_keeper', 'Fish Keeper'),
        ('small_pet_owner', 'Small Pet Owner'),
        ('pet_adopter', 'Pet Adopter'),
        ('new_pet_owner', 'New Pet Owner'),
    ], string='Reviewer Type', default='verified', required=True,
        help="Shown under the reviewer name on the /reviews page;"
             " chosen by the customer in the review form.")
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending', required=True, index=True,
        help="Only approved reviews are shown on the /reviews page.")

    _rating_range = models.Constraint(
        'CHECK(rating >= 1 AND rating <= 5)',
        'The rating must be between 1 and 5.',
    )

    def action_approve(self):
        """Approve the reviews: they are shown on the /reviews page."""
        self.write({'state': 'approved'})

    def action_reject(self):
        """Reject the reviews: they are not shown on the website."""
        self.write({'state': 'rejected'})

    def action_reset_to_pending(self):
        """Set the reviews back to pending (hidden until approved again)."""
        self.write({'state': 'pending'})
