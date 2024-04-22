# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info(f'Starting migration from version {version}')

    cr.execute(
        """ALTER TABLE IF EXISTS field_widgets RENAME TO field_widget;
        UPDATE ir_model SET model = 'field.widget' WHERE model = 'field.widgets';
        UPDATE ir_model_data SET name = 'model_field_widget' WHERE model = 'ir_model' AND name = 'model_field_widgets';
        UPDATE ir_model_data SET model = 'field.widget' WHERE model = 'field.widgets';
        """)
    _logger.info('Migration completed')
