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
#############################################################################
import random

from odoo import models


class ProjectProject(models.Model):
    """This class inherits from 'project.project' and adds custom functionality
    to it. It provides methods to work with project data."""
    _inherit = 'project.project'

    def get_color_code(self):
        """Generate a random color code in hexadecimal format.
        :return: A random color code in the format '#RRGGBB.'"""
        return f"#{random.randint(0, 0xFFFFFF):06x}"
