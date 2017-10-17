# -*- encoding: utf-8 -*-
##############################################################################
#
#    Hardware Customer Display module for Odoo
#    Copyright (C) 2014 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Hardware Customer Display BA6X',
    'version': '8.0.0.1.0',
    'category': 'Hardware Drivers',
    'license': 'AGPL-3',
    'summary': 'Adds support for Customer Display BA6x in the Point of Sale',
    'description': """
Hardware Customer Display - Wincor Nixdorf 
=========================
This module support hardware display from  Wincor Nixdorf models BA6x, full
language support, like cyrrilic and more.
    """,
    'author': "Rosen Vladimirov",
    'depends': ['hw_proxy'],
    'external_dependencies': {
        'python': ['unidecode'],
    },
    'data': [],
}
