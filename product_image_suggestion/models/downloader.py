# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Vishnu kp(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from pathlib import Path
import shutil
import sys

try:
    from bing import Bing
except ImportError:
    from .bing import Bing


def download(query, limit=100, output_dir='dataset', adult_filter_off=True,
             force_replace=False, timeout=60, filter="", verbose=True):
    """download the images within the limit provided"""
    if adult_filter_off:
        adult = 'off'
    else:
        adult = 'on'
    image_dir = Path(output_dir).joinpath(query).absolute()
    if force_replace:
        if Path.isdir(image_dir):
            shutil.rmtree(image_dir)
    try:
        if not Path.is_dir(image_dir):
            Path.mkdir(image_dir, parents=True)
    except Exception:
        sys.exit(1)
    bing = Bing(query, limit, image_dir, adult, timeout, filter, verbose)
    return bing.run()
