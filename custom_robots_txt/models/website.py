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
from odoo import fields, models


class Website(models.Model):
    """Inherits the 'website' model to add a 'mode' selection field used to
    control the robots.txt indexing behaviour for search engine crawlers.

    The 'mode' field determines how the robots.txt file is generated:
      - 'custom'      : User-defined directives via the wizard.
      - 'allow_all'   : Allows all search engine crawlers to index the site.
      - 'disallow_all': Blocks all search engine crawlers from indexing.
    """

    _inherit = "website"

    mode = fields.Selection(
        selection=[
            ('custom', 'Custom'),
            ('allow_all', 'Allow All'),
            ('disallow_all', 'Disallow All'),
        ],
        string="Robots Mode",
        help="Select the mode of the robots.txt file that controls which "
             "parts of the website are accessible to search engine crawlers.",
    )
