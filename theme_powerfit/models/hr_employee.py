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
"""Extension of hr.employee with Gym Trainer fields for PowerFit theme."""

from odoo import fields, models


class HrEmployee(models.Model):
    """Extend hr.employee with gym trainer attributes for the PowerFit website."""

    _inherit = 'hr.employee'

    # ─── Gym Trainer Toggle ───────────────────────────────────────────────────
    is_gym_trainer = fields.Boolean(
        string='Gym Trainer',
        default=False,
        help='Enable to mark this employee as a Gym Trainer displayed on the website.',
    )

    # ─── Trainer Information ──────────────────────────────────────────────────
    trainer_short_description = fields.Text(
        string='Short Description',
        help='A short bio shown on the trainer card hover overlay.',
    )
    trainer_experience = fields.Integer(
        string='Years of Experience',
        default=0,
        help='Number of years the trainer has been coaching.',
    )
    trainer_clients = fields.Integer(
        string='Clients Trained',
        default=0,
        help='Total number of clients this trainer has worked with.',
    )
    trainer_rating = fields.Float(
        string='Rating',
        digits=(3, 1),
        default=0.0,
        help='Trainer rating displayed on the website (0.0 – 5.0).',
    )

    # ─── Social Media Links ───────────────────────────────────────────────────
    trainer_instagram = fields.Char(
        string='Instagram URL',
        help='Full Instagram profile URL (e.g. https://instagram.com/username).',
    )
    trainer_twitter = fields.Char(
        string='Twitter / X URL',
        help='Full Twitter/X profile URL (e.g. https://twitter.com/username).',
    )
    trainer_linkedin = fields.Char(
        string='LinkedIn URL',
        help='Full LinkedIn profile URL (e.g. https://linkedin.com/in/username).',
    )
