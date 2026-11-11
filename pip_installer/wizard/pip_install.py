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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import subprocess
import sys
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class PipInstall(models.TransientModel):
    """Class for executing terminal pip commands from wizard."""
    _name = 'pip.install'
    _description = 'Pip Installer'

    name = fields.Char(
        string='Command',
        required=True,
        help='Write the pip command to execute.')

    def action_done(self):
        """Execute pip command and display output in dialog."""
        self.ensure_one()
        command = (self.name or '').strip()
        if not command.startswith("pip"):
            raise ValidationError(_('Please enter a proper pip command'))
        process = subprocess.Popen(['yes'], stdout=subprocess.PIPE)
        try:
            executable_command = f'"{sys.executable}" -m {command}'
            result = subprocess.run(
                executable_command,
                shell=True,
                check=True,
                stdin=process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            output_message = result.stdout or _('Successfully Executed')
            message = self.env['import.message'].create([{'message': output_message}])
            return {
                'name': _('Successfully Executed'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'import.message',
                'res_id': message.id,
                'target': 'new',
            }
        except (subprocess.CalledProcessError, TypeError):
            raise ValidationError(_('Please enter a proper pip command'))
        finally:
            try:
                process.kill()
            except OSError:
                pass
