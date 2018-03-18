# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Author: Rosen Vladimirov vladimirov.rosen@gmail.com
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
    'name': 'POS Taxes repair',
    'version': '8.0.0.1.0',
    'category': 'Point Of Sale',
    'summary': 'Fix all taxes in PO',
    'description': """
        Repair all fiscal position and taxes in pos order.
        """,
    'author': 'Rosen Vladimirov',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        'views/point_of_sale_view.xml',
    ],
    'demo': [
    ],
    'test': [

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': [],
}
