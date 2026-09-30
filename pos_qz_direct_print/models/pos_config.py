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
from odoo import models, fields, api
import base64
import subprocess
import tempfile
import logging

_logger = logging.getLogger(__name__)

class PosConfig(models.Model):
    """Extends POS configuration to support direct silent printing
        via a CUPS-compatible system printer."""
    _inherit = 'pos.config'

    system_printer_name = fields.Char("System Printer Name", help="Name of the printer in CUPS")

    @api.model
    def action_print_to_system(self, config_id, base64_image):
        """Print the base64-encoded receipt image to the configured CUPS printer."""
        config = self.browse(config_id)
        if not config.system_printer_name:
            _logger.warning("No system printer name configured for this POS.")
            return False

        try:
            image_data = base64.b64decode(base64_image)
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(image_data)
                temp_file_path = temp_file.name

            print_command = ['lp', '-d', config.system_printer_name, '-o', 'fit-to-page', temp_file_path]
            
            _logger.info(f"Executing print command: {' '.join(print_command)}")
            result = subprocess.run(print_command, capture_output=True, text=True)

            if result.returncode != 0:
                _logger.error(f"Failed to print receipt: {result.stderr}")
                return False
                
            _logger.info(f"Successfully sent receipt to {config.system_printer_name}. Output: {result.stdout}")
            return True

        except Exception as e:
            _logger.error(f"Exception during system print: {e}")
            return False
