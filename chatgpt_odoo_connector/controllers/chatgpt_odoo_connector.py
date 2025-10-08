# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from pathlib import Path
from odoo.http import request
import os
from odoo.tools import json


class SpeechToText(http.Controller):
    @http.route('/upload_audio', type='http', auth='public', methods=['POST'], csrf=False)
    def upload_audio(self, **kwargs):
        """
            Function for uploading audio file into a file and
            returns the path of the file as json format
        """
        upload_dir = Path(__file__).parent
        file = kwargs.get('file')
        if file:
            file_path = os.path.join(upload_dir, file.filename)
            with open(file_path, 'wb') as f:
                f.write(file.read())
            return request.make_response(json.dumps({'filePath': file_path}), headers={'Content-Type': 'application/json'})
        return request.make_response(json.dumps({'error': 'No file uploaded'}), headers={'Content-Type': 'application/json'})
