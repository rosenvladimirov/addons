# *- encoding: utf-8 -*-
##############################################################################
#
#    Product - Average Consumption Module for Odoo
#    Copyright (C) 2013-Today GRAP (http://www.grap.coop)
#    @author Julien WESTE
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
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

from openerp import models, fields, api

DOMAIN_RANGE = [
    ('team', 'By Teams'),
    ('warehous', 'By Warehouses'),
]


class ProductConsumption(models.Model):
    _name = "product.consumption"

    # Columns section
    product_id = fields.Many2one(
        comodel_name='product.product', string='Product',
        required=True, ondelete='cascade')
    company_id = fields.Many2one(
        'res.company', related='product_id.company_id')
    product_tmpl_id = fields.Many2one(
        'product.template', related='product_id.product_tmpl_id',
        string='Template', store=True)
    location_id = fields.Many2one(
        'stock.location', string='Location', required=True,
        ondelete='cascade')
    outgoing_qty = fields.Float("Outgoing quantity", default=0)
    nb_days = fields.Integer(
        string='Number of days for the calculation',
        help="""The calculation will be done according to Calculation Range"""
        """ field or since the first stock move of the product if it's"""
        """ more recent""")
