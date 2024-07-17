# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
    model to set up the import/export history related to hubspot connector """
    _name = 'hubspot.sync.history'
    _description = 'Sync History'
    _rec_name = 'record_name'

    record_name = fields.Char(string="Record Name", compute='_compute_rec_name',
                              help="To show unique record name")
    date = fields.Date(
        string="Sync Date",
        help="The date of the synchronization for this record.")
    res_model_id = fields.Many2one(comodel_name='ir.model', string="Model",
                                   help="The model associated with this record")
    sync_mode = fields.Selection(
        selection=[
            ('import', 'Imported'),
            ('export', 'Exported'),
            ('hub_updated', 'Hubspot Updated'),
            ('odoo_updated', 'Odoo Updated')],
        string='Sync Mode',
        help="The synchronization mode for the record.")
    state = fields.Selection(
        selection=[('success', 'Success'), ('error', 'Failed')],
        string='Status', readonly=True, required=True,
        copy=False, help="The status of the synchronization process.")
    count = fields.Integer(string="Count",
                           help="The count associated with this record.")
    error = fields.Text(string="Reason",
                        help="The reason for any errors or failures that "
                             "occurred during synchronization.")

    @api.depends('date', 'res_model_id', 'count')
    def _compute_rec_name(self):
        for rec in self:
            rec.record_name = (f"{self.date}"
                               f" : {self.res_model_id.name}-{self.count}")
