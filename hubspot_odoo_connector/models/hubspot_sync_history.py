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
from odoo import api, fields, models


class HubspotSyncHistory(models.Model):
    """
    Stores the history of data synchronization between Odoo and HubSpot, including sync date, model, mode, status, record count, and error details.
    """
    _name = 'hubspot.sync.history'
    _description = 'Sync History'
    _rec_name = 'record_name'

    record_name = fields.Char(
        string="Record Name",
        compute='_compute_rec_name',
        store=True
    )

    date = fields.Datetime(
        string="Sync Date",
        help="The date and time of this synchronization"
    )

    res_model_id = fields.Many2one(
        comodel_name='ir.model',
        string="Model",
        help="The related model"
    )

    sync_mode = fields.Selection([
        ('import', 'Imported'),
        ('export', 'Exported'),
        ('hub_updated', 'Hubspot Updated'),
        ('odoo_updated', 'Odoo Updated')
    ], string="Sync Mode")

    state = fields.Selection([
        ('success', 'Success'),
        ('error', 'Failed')
    ], string="Status", readonly=True, required=True)

    count = fields.Integer(string="Count")

    error = fields.Text(string="Reason")

    @api.depends('date', 'res_model_id', 'count')
    def _compute_rec_name(self):
        """
        Computes a readable display name for each sync record using the sync date, related model name, and record count.
        """
        for rec in self:
            if rec.date and rec.res_model_id and rec.count is not None:
                rec.record_name = f"{rec.date} : {rec.res_model_id.name} - {rec.count}"
            else:
                rec.record_name = "History"
