# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
from odoo import fields, models


class DbBackupHistory(models.Model):
    """Log of every automatic or manual database backup run."""
    _name = 'db.backup.history'
    _description = 'Database Backup History'
    _order = 'backup_date desc, id desc'

    configure_id = fields.Many2one(
        'db.backup.configure', string='Backup Configuration',
        required=True, ondelete='cascade', index=True,
        help='The backup configuration this run belongs to.')
    db_name = fields.Char(string='Database',
                          help='Database that was backed up in this run.')
    name = fields.Char(string='Backup Filename',
                       help='Name of the generated backup file.')
    backup_date = fields.Datetime(string='Date', default=fields.Datetime.now,
                                  help='When the backup run happened.')
    backup_destination = fields.Selection(
        selection='_selection_backup_destination', string='Destination',
        help='Destination the backup was sent to.')
    status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Status', help='Result of the backup run.')
    is_manual = fields.Boolean(
        string='Manual', help='Whether this run was triggered manually.')
    duration = fields.Float(
        string='Duration (s)', help='Duration of the run in seconds.')
    message = fields.Text(
        string='Message', help='Error message when the backup failed.')

    def _selection_backup_destination(self):
        """Reuse the destination selection from the backup configuration."""
        return self.env['db.backup.configure']._fields[
            'backup_destination'].selection
