# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
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
    'name': 'Sales Loyalty Program POS',
    'version': '0.1',
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'category': 'sale',
    'summary': 'Loyalty Program for POS Orders',
    'description': """
Define loyalty programs to enable customers to colletc points and earn rewards. This modules is for POS.

""",
    'depends': ['sale_loyalty','pos_partner'],
    'data': [
        'sale_loyalty_view.xml',
    ],
    'installable': True,
    'autoinstall': True,
}
