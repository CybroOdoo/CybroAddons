# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import os
import platform
import psycopg2
import psutil
from odoo import api, models
from odoo.exceptions import AccessError
from odoo.tools import config


def get_model_storage(db_name, model_name):
    """ Method to get storage usage of a model it returns storage of
    specific model passed to this method """
    sql_model_name = model_name.replace(".", "_")
    db_host = config['db_host']
    db_port = config['db_port']
    db_user = config['db_user']
    db_password = config['db_password']
    try:
        connection = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT sum(pg_column_size(x)) 
            FROM (SELECT * FROM {sql_model_name}) AS x;
        """)
        total_storage = cursor.fetchone()[0]
        cursor.close()
        connection.close()
    except psycopg2.Error as e:
        if 'relation does not exist' in str(e).lower():
            # Return zero as storage when the relation doesn't exist
            return '0 bytes'
        else:
            return None
    return total_storage


def get_index_data(db_name, model_name):
    sql_model_name = model_name.replace(".", "_")
    db_host = config['db_host']
    db_port = config['db_port']
    db_user = config['db_user']
    db_password = config['db_password']
    try:
        connection = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        cursor = connection.cursor()
        cursor.execute(f"""SELECT
                    pg_indexes_size('{sql_model_name}');
                """)
        index_size = cursor.fetchone()[0]
        cursor.close()
        connection.close()
    except psycopg2.Error as e:
        if 'relation does not exist' in str(e).lower():
            # Return zero as storage when the relation doesn't exist
            return '0 bytes'
        else:
            return None
    return index_size


class StorageUsage(models.Model):
    """ Model for Compute Storage usage of each models """
    _name = 'storage.usage'
    _description = "Storage Usage"

    @api.model
    def get_data(self):
        """ Method for get all existing models and return model with its
        storage with the help of get_model_storage_method """
        user_group_ids = self.env.user.groups_id.ids
        accessible_model_ids = self.env['ir.model.access'].search([
            ('group_id', 'in', user_group_ids)
        ]).mapped('model_id').ids
        model_names = [record.model for record in self.env['ir.model'].browse(
            accessible_model_ids)]
        chart_x = []
        chart_y = []
        for name in model_names:
            size = get_model_storage(self.env.cr.dbname, name) if get_model_storage(self.env.cr.dbname, name) else 0
            if size > 100000:
                size = round(size / (1024 * 1024), 2)
                if size != 0:
                    chart_x.append(name)
                    chart_y.append(size)
        return {'x_data': chart_x,
                'y_data': chart_y}

    @api.model
    def get_info(self):
        """
        Method for get database information and returns it as a dictionary
        """
        db_host = config['db_host']
        db_port = config['db_port']
        db_user = config['db_user']
        db_password = config['db_password']
        try:
            connection = psycopg2.connect(
                dbname=self.env.cr.dbname,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port
            )
        # Establishing connection
            cursor = connection.cursor()
        # Fetching version od DB
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
        # Fetching total size of DB
            cursor.execute("""
                SELECT sum(pg_total_relation_size(schemaname || '.' || 
                tablename)) FROM pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema');
            """)
            db_size = cursor.fetchone()[0] / (1024 * 1024)
        # Fetching count of tables in DB
            cursor.execute("""
                SELECT count(*) FROM information_schema.tables WHERE 
                table_schema='public';
            """)
            db_tables = cursor.fetchone()[0]
        # Closing the connection
            cursor.close()
            connection.close()
        #   Getting system monitor datas
            system_datas = dict(psutil.virtual_memory()._asdict())
            total_memory = system_datas['total'] / (1024 * 1024 * 1024)
            used_memory = system_datas['used'] / (1024 * 1024 * 1024)
            available_memory = system_datas['available'] / (1024 * 1024 * 1024)
            cpu_usage = psutil.cpu_percent(interval=None)
            operating_system = platform.system()
            os_ver = platform.release()
            soft_limit = config.get('limit_memory_soft') / (1024 * 1024 * 1024)
            hard_limit = config.get('limit_memory_hard') / (1024 * 1024 * 1024)
            transient_age_limit = config.get('transient_age_limit')
            limit_time_cpu = config.get('limit_time_cpu')
            limit_request = config.get('limit_request')
            limit_time_real = config.get('limit_time_real')
            http_port = config.get('http_port')
            db_user = config.get('db_user')
            # Odoo ram usage
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            ram_usage = memory_info.rss / (1024 * 1024)

            db_date = self.env['ir.config_parameter'].sudo().get_param(
                'database.create_date')
        except psycopg2.Error as e:
            raise AccessError(
                f"Error while fetching database information via query: {e}")
        return {
            'db_name': self.env.cr.dbname,
            'db_version': db_version,
            'db_date': db_date,
            'db_size': f"{round(db_size, 2)} MB",
            'db_tables': db_tables,
            'total_memory': f"{round(total_memory, 2)} GB",
            'used_memory': f"{round(used_memory, 2)} GB",
            'available_memory': f"{round(available_memory, 2)} GB",
            'cpu_usage': f"{cpu_usage} %",
            'ram_usage': f"{round(ram_usage, 2)} MB",
            'os': f"{operating_system +' ' + os_ver}",
            'db_user': db_user,
            'soft_limit': f"{soft_limit} GB",
            'hard_limit': f"{hard_limit} GB",
            'transient_age_limit': f"{transient_age_limit} GB",
            'limit_time_cpu': f"{limit_time_cpu} s",
            'limit_request': limit_request,
            'limit_time_real': limit_time_real,
            'http_port': http_port,
        }
