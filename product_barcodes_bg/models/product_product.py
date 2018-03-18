# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2015 ERP|OPEN (www.erpopen.nl).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from itertools import repeat

_logger = logging.getLogger(__name__)

domain_old = []

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.one
    @api.depends('barcode_ids.name')
    def _get_barcodes(self):
        barcode_list=[]
        for barcode in self.barcode_ids:
            barcode_list.append(barcode.name)

        self.ean13=str(barcode_list)

    barcode_ids = fields.One2many(
        comodel_name="product.barcode",
        inverse_name="product_id",
        string='Barcodes'
    )
    ean13 = fields.Char(
            compute="_get_barcodes",
            string="Barcodes",
            size=200,
            readonly=True,
            store=True
    )

    @api.one
    @api.depends('barcode_ids.name')
    def _get_barcodes(self):
        barcode_list=''
        for barcode in self.barcode_ids:
            if not barcode_list:
                barcode_list = barcode.name
            else:
                barcode_list += ', ' + barcode.name

        self.ean13=str(barcode_list)

    @api.model
    def search(self, domain, *args, **kwargs):
        global domain_old
        if filter(lambda x: x[0] == 'ean13', domain):
            _logger.info("Start Filter %s:%s" % (domain, domain_old))
            counter = len(filter(lambda x: x[0] == 'ean13', domain))
            if counter > 1:
                j = 0
                for i,x in enumerate(domain):
                    if x[0] == 'ean13' and j < counter-1:
                        #_logger.info("domain %s:%s:%s" % (x[0], i, j))
                        domain[i] = domain_old[j]
                        j += 1
            else:
                domain_old = []
            barcode_operator = filter(lambda x: x[0] == 'ean13', domain)[0][1]
            barcode_operator = (barcode_operator == '=') and 'ilike' or barcode_operator
            barcode_value = filter(lambda x: x[0] == 'ean13', domain)[0][2]
            if len(filter(lambda x: x[0] == 'default_code', domain)) == 0:
                domain += [('default_code','ilike', barcode_value)]
            barcodes = self.env['product.barcode'].search(
                    [('name', barcode_operator, barcode_value)])
            domain = filter(lambda x: x[0] != 'barcode', domain)
            suppliercode = self.env['product.supplierinfo'].search(
                    [('product_code', barcode_operator, barcode_value)])
            domain = filter(lambda x: x[0] != 'product_tmpl_id', domain)
            _logger.info("Filter %s:%s" % (domain, suppliercode))
            domain_old.append(('barcode_ids', 'in', barcodes.ids))
            domain_old.append(('product_tmpl_id', 'in', [x.product_tmpl_id.id for x in suppliercode]))
            domain += [domain_old[-2]]
            domain += [domain_old[-1]]
            if len(filter(lambda x: isinstance(x, str), domain)) == 0:
                domain = list(repeat('|',len(filter(lambda x: isinstance(x, tuple), domain))-1))+filter(lambda x: isinstance(x, tuple), domain)+filter(lambda x: isinstance(x, list), domain)
            _logger.info("After Filter %s:%s" % (domain, domain_old))
        return super(ProductProduct, self).search(domain, *args, **kwargs)
