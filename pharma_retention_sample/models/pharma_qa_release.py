# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class PharmaQaRelease(models.Model):
    """Surfaces the Retention Sample action on the released QA record as well."""
    _inherit = 'pharma.qa.release'

    show_retain_sample = fields.Boolean(related='lot_id.show_retain_sample',
                                        help='The released batch still needs a reserve sample.')
    retention_sample_count = fields.Integer(related='lot_id.retention_sample_count',
                                            string='Retention Samples',
                                            help='Reserve samples of the batch.')

    def action_create_retention_sample(self):
        """Create the released batch's draft reserve sample."""
        self.ensure_one()
        return self.lot_id.action_create_retention_sample()

    def action_view_retention_samples(self):
        """Open the batch's reserve samples."""
        self.ensure_one()
        return self.lot_id.action_view_retention_samples()
