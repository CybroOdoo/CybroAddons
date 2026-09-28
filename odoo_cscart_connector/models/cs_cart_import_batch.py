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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields, api


class CsCartImportBatch(models.Model):
    """
    CS-Cart Import Batch Model.

    Stores audit logs, execution statuses, timestamps, and bus notifications
    for background and manual import batch operations from CS-Cart.
    """
    _name = 'cs.cart.import.batch'
    _description = 'CS-Cart Import Batch'
    _order = 'create_date desc'

    name = fields.Char(string='Name', required=True)
    import_type = fields.Selection([
        ('categories', 'Categories'),
        ('attributes', 'Attributes'),
        ('products', 'Products'),
        ('customers', 'Customers'),
        ('orders', 'Orders')
    ], string='Import Type', required=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='pending')
    log_notes = fields.Html(string='Logs')
    create_date = fields.Datetime(string='Created On', readonly=True)
    queue_job_id = fields.Many2one('queue.job', string='Related Queue Job', readonly=True)
    cs_cart_config_id = fields.Many2one('cs.cart.config', string='CS-Cart Store')

    def button_cancel(self):
        """
        Cancel the ongoing import batch operation and update associated queue job.
        """
        for record in self:
            if record.queue_job_id:
                record.queue_job_id.button_cancelled()
            record.write({
                'state': 'cancelled',
                'log_notes': (record.log_notes or '') + '<p class="text-warning">⚠️ Import manually cancelled by user.</p>'
            })

    @api.model_create_multi
    def create(self, vals_list):
        """
        Create import batch records and broadcast real-time reload signals to client UI.

        :param vals_list: List of field value dictionaries for creation
        :type vals_list: list[dict]
        :return: Created cs.cart.import.batch records
        :rtype: cs.cart.import.batch
        """
        records = super().create(vals_list)
        for record in records:
            payload = {
                'id': record.id,
                'name': record.name,
                'import_type': record.import_type,
                'state': record.state,
            }
            self.env['bus.bus']._sendone('broadcast', 'cs_cart_import_batch_reload', payload)
        return records

    def write(self, vals):
        """
        Update import batch records and sync status message to parent store config instance.

        :param vals: Field values dictionary to update
        :type vals: dict
        :return: Result of super write call
        :rtype: bool
        """
        res = super().write(vals)
        if 'state' in vals:
            new_state = vals['state']
            for record in self:
                if record.cs_cart_config_id:
                    if new_state == 'done':
                        record.cs_cart_config_id.write({
                            'last_sync_status': 'success',
                            'last_sync_message': f'{record.import_type.capitalize()} import completed successfully.'
                        })
                        record.cs_cart_config_id.message_post(
                            body=f"CS-Cart Import Batch '{record.name}' completed successfully."
                        )
                    elif new_state == 'failed':
                        error_msg = f'{record.import_type.capitalize()} import failed.'
                        record.cs_cart_config_id.write({
                            'last_sync_status': 'failed',
                            'last_sync_message': error_msg
                        })
                        record.cs_cart_config_id.message_post(
                            body=f"❌ CS-Cart Import Batch '{record.name}' failed. Please check the logs."
                        )

        if 'state' in vals or 'log_notes' in vals:
            for record in self:
                payload = {
                    'id': record.id,
                    'name': record.name,
                    'import_type': record.import_type,
                    'state': record.state,
                }
                self.env['bus.bus']._sendone('broadcast', 'cs_cart_import_batch_reload', payload)
        return res
