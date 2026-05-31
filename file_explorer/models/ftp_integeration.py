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
from odoo import models, api
import paramiko


class FtpIntegration(models.Model):
    """
    New model is created to make connection to server and download
     file from the server to local
    """
    _name = 'ftp.integration'
    _description = 'FTP Integration'

    @api.model
    def get_directories_local(self):
        """
        Initially Gets the directories of the local , if it's a file then
        file type is changes as txt and returned to js
        """
        base_directory = '/'
        full_path = os.path.join(base_directory)
        if not os.path.exists(full_path):
            return {'files': []}

        files = os.listdir(full_path)

        file_list = []
        for file in files:
            file_path = os.path.join(full_path, file)
            if os.path.isdir(file_path):
                file_type = 'directory'
            else:
                file_type = 'txt'
            file_list.append({'name': file, 'path': os.path.join('/', file),
                              'type': file_type, 'remote': 'false'})

        return {'files': file_list}


    @api.model
    def get_file_detailed_local(self, directory_path):
        """
         Gets the directories of the local , if it's a file then file type is
         changes as txt and returned to js
        """
        base_directory = directory_path
        if directory_path is None:
            directory_path = ''

        full_path = os.path.join(base_directory, directory_path)

        if not os.path.exists(full_path):
            return {'files': []}

        files = os.listdir(full_path)

        file_list = []
        for file in files:
            file_path = os.path.join(full_path, file)
            if os.path.isdir(file_path):
                file_type = 'directory'
            else:
                file_type = 'txt'
            file_list.append({'name': file,
                              'path': os.path.join(directory_path, file),
                              'type': file_type,
                              'remote': 'false'})

        return {'files': file_list}


    @api.model
    def get_remote_file_details(self, host, user_name, password, port, path):
        """
         Gets the directories of the remote , if it's a file then file type
         is changes as txt and returned to js
        """
        result = self.env['ftp.integration'].get_remote_subfiles(host, user_name,
                                                                 password, port, path)
        return {'remote_files': result}


    @api.model
    def connect_remote(self, host, user, password, port_number):
        """
        Using SSH the connection to the remote is made
        """
        result = self.env['ftp.integration'].connect_ssh(host, user, password,
                                                         port_number)
        print(result, "res")
        return {'files_list': result['directories'],
                "connect_status": result['status']}

    def connect_ssh(self, host, username, password, port):
        """
        Connection to the remote is eshtablished from here using host , password, user and port and using ssh connection
        made into the remote
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=host, port=port, username=username,
                        password=password)

            # Get the current working directory
            stdin, stdout, stderr = ssh.exec_command('pwd')
            current_directory = stdout.read().decode().strip()

            # List details of the current directory and its subdirectories
            stdin, stdout, stderr = ssh.exec_command('ls -ld . */')
            output = stdout.read().decode()

            directories = self.parse_ls_output(output, current_directory)

            # Check file types and categorize them
            for directory in directories:
                if directory['type'] == 'directory':
                    directory['type'] = 'directory'
                else:
                    directory['type'] = 'txt'

            return {'status': 'success', 'directories': directories}

        except Exception as e:
            return {'status': 'error', 'message': f"Connection failed: {str(e)}"}

    def parse_ls_output(self, output, current_directory):
        """
        Used to parse through files and check whether it is a file or directory
        and if it is a file change file type to
        txt else it's file type is changed to directory
        """
        directories = []
        lines = output.splitlines()

        for line in lines:
            parts = line.split()
            if len(parts) >= 9:
                file_type = parts[0][0]  # The first character in the
                # permission string indicates the file type
                name = parts[-1]

                # Remove trailing '/' from directory names
                if name.endswith('/'):
                    name = name.rstrip('/')

                if file_type == 'd':
                    directories.append({'name': name,
                                        'path': f"{current_directory}/{name}",
                                        'type': 'directory'})
                else:
                    directories.append({'name': name,
                                        'path': f"{current_directory}/{name}",
                                        'type': 'file'})

        return directories

    def get_remote_subfiles(self, host, username, password, port, path):
        """
          Using SSH get connection and get remote sub files

        """
        subfiles = []

        try:
            # Create an SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the server
            ssh.connect(host, port, username, password)

            # Execute the command to list files in the directory
            stdin, stdout, stderr = ssh.exec_command(f'ls -l {path}')

            # Read the command output
            lines = stdout.readlines()


            # Check if output is received
            if not lines:
                raise Exception("No output received from the server. "
                                "Please check the directory path.")

            # Process each line of the output, skipping the first line (total)
            for line in lines[1:]:
                parts = line.split(maxsplit=8)  # Use maxsplit to correctly handle filenames with spaces
                if len(parts) < 9:
                    continue  # Skip lines that don't match expected format

                file_type = 'directory' if parts[0][0] == 'd' else 'file'
                file_name = parts[-1].strip().rstrip('/')  # Remove trailing slash and strip any newlines or spaces

                # Append file information to subfiles
                subfiles.append({'name': file_name, 'type': file_type,
                                 'path': f"{path}/{file_name}"})

            # Close the connection
            ssh.close()

        except Exception as e:
            subfiles.append({'error': str(e)})

        return subfiles

    def download_to_local(self, host, user, password, port, remote_path, local_path):
        """
        Using SSH and SFTP, the file from remote is downloaded into the local
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=port, username=user, password=password)
            sftp = ssh.open_sftp()
            try:
                sftp.stat(remote_path)
                if local_path.endswith('/'):
                    raise ValueError("Local path must include the filename, "
                                     "not just the directory.")
                sftp.get(remote_path, local_path)
            finally:
                sftp.close()
            ssh.close()
            return {'status': 'success',
                    'message': 'File downloaded successfully'}

        except Exception as e:

            return {'status': 'error', 'message': f'Error: {str(e)}'}
