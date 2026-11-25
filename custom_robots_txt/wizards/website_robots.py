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
"""Website Robots Transient Model Extension."""
from odoo import api, fields, models


class Robots(models.TransientModel):
    """Extends the 'website.robots' transient model to introduce a 'mode'
    selection field that pre-populates the robots.txt content based on the
    currently selected indexing strategy.

    Supported modes:
      - 'custom'      : Allows the user to manually define robots.txt content.
      - 'allow_all'   : Pre-fills the content to permit all crawlers.
      - 'disallow_all': Pre-fills the content to block all crawlers.

    The wizard saves the selected mode and custom content back to the
    active website record upon confirmation.
    """

    _inherit = "website.robots"

    content = fields.Text(
        default=lambda self: (
            self.env.website or self.env['website'].search([], limit=1)
        ).robots_txt,
    )
    mode = fields.Selection(
        selection=[
            ('custom', 'Custom'),
            ('allow_all', 'Allow All'),
            ('disallow_all', 'Disallow All'),
        ],
        default=lambda self: (
            self.env.website or self.env['website'].search([], limit=1)
        ).mode,
        help="Select the mode of the robots.txt file that controls indexing "
             "for search engine crawlers.",
    )

    @api.onchange('mode')
    def _onchange_mode(self):
        """Populate the robots.txt content field based on the selected mode.

        When the mode changes:
          - 'custom'      : Restores the existing website content or sets a space
                            if empty.
          - 'allow_all'   : Overwrites the content with a universal Allow rule.
          - 'disallow_all': Overwrites the content with a universal Disallow rule.
        """
        website = self.env.website or self.env['website'].search([], limit=1)
        if self.mode == 'custom':
            self.content = website.robots_txt or " "
        elif self.mode == 'allow_all':
            self.content = "User-agent: *\nAllow: /"
        elif self.mode == 'disallow_all':
            self.content = "User-agent: *\nDisallow: /"

    def action_save(self):
        """Save the robots.txt content and mode back to the active website.

        Calls the parent ``action_save`` to persist the robots.txt content,
        then updates the ``mode`` field on the current website record so the
        selected strategy is retained across sessions.

        Returns:
            dict: The action dictionary returned by the parent method.
        """
        res = super().action_save()
        website = self.env.website or self.env['website'].search([], limit=1)
        website.mode = self.mode
        website.robots_txt = self.content
        return res
