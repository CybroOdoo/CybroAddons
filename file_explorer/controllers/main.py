# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Afthab K Naufal @cybrosys (odoo@cybrosys.com)
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
import os
import paramiko
from odoo import http
from odoo.http import request

class Main(http.Controller):
    @http.route('/filepond/process', type='http', auth='user',
                methods=['POST'], csrf=False)
    def filepond_process(self):
        """
        The file uploaded in the filepond div is uploaded into the remote server
        """
        # Retrieve the uploaded file from the request
        filepond = request.params.get('filepond')

        # Retrieve the additional parameters
        host = request.params.get('host')
        username = request.params.get('username')
        password = request.params.get('password')
        port = int(request.params.get('port', 22))  # Default to port 22 if not provided
        upload_location = request.params.get('upload_location')  # The remote upload directory

        if filepond:
            # Save the file temporarily on the local server
            file_path = '/tmp/' + filepond.filename
            with open(file_path, 'wb') as f:
                f.write(filepond.read())

            # Setup SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            try:
                # Connect to the remote server
                ssh.connect(host, port=port, username=username,
                            password=password)

                # Open SFTP session
                sftp = ssh.open_sftp()
                try:
                    sftp.chdir(upload_location)  # Try to change to the directory
                except IOError as e:
                    # If the directory doesn't exist, return an error
                    if e.errno == 2:  # No such file or directory
                        return (f"Upload location '{upload_location}' does not "
                                f"exist on the remote server.")
                    else:
                        raise

                # Transfer the file to the specified upload location
                remote_file_path = os.path.join(upload_location,
                                                filepond.filename)
                sftp.put(file_path, remote_file_path)
                sftp.close()

                # Optionally, remove the local file after transfer
                os.remove(file_path)

                return "File uploaded and transferred successfully!"
            except Exception as e:
                return str(e)
            finally:
                ssh.close()
        return "No file uploaded."
