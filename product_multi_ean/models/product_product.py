# -*- coding: utf-8 -*-
# © 2012-2014 Guewen Baconnier (Camptocamp SA)
# © 2015 Roberto Lizana (Trey)
# © 2016 Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
from openerp.addons.product import product as addons_product
import operator

import logging
_logger = logging.getLogger(__name__)

CONSTRAINT_MESSAGE = 'Error: Invalid EAN/GTIN code'
HELP_MESSAGE = ("EAN8 EAN13 UPC JPC GTIN \n"
                "http://en.wikipedia.org/wiki/Global_Trade_Item_Number")
domain_old = []

def is_pair(x):
    return not x % 2


def check_ean8(eancode):
    """Check if the given ean code answer ean8 requirements
    For more details: http://en.wikipedia.org/wiki/EAN-8

    :param eancode: string, ean-8 code
    :return: boolean
    """
    if not eancode or not eancode.isdigit():
        return False

    if not len(eancode) == 8:
        _logger.warn('Ean8 code has to have a length of 8 characters.')
        return False

    sum = 0
    ean_len = int(len(eancode))
    for i in range(ean_len-1):
        if is_pair(i):
            sum += 3 * int(eancode[i])
        else:
            sum += int(eancode[i])
    check = 10 - operator.mod(sum, 10)
    if check == 10:
        check = 0

    return check == int(eancode[-1])

def check_upc(upccode):
    """Check if the given code answers upc requirements
    For more details:
    http://en.wikipedia.org/wiki/Universal_Product_Code

    :param upccode: string, upc code
    :return: bool
    """
    if not upccode or not upccode.isdigit():
        return False

    if not len(upccode) == 12:
        _logger.warn('UPC code has to have a length of 12 characters.')
        return False

    sum_pair = 0
    ean_len = int(len(upccode))
    for i in range(ean_len-1):
        if is_pair(i):
            sum_pair += int(upccode[i])
    sum = sum_pair * 3
    for i in range(ean_len-1):
        if not is_pair(i):
            sum += int(upccode[i])
    check = ((sum/10 + 1) * 10) - sum

    return check == int(upccode[-1])

def check_ean13(eancode):
    """Check if the given ean code answer ean13 requirements
    For more details:
    http://en.wikipedia.org/wiki/International_Article_Number_%28EAN%29

    :param eancode: string, ean-13 code
    :return: boolean
    """
    if not eancode or not eancode.isdigit():
        return False

    if not len(eancode) == 13:
        _logger.warn('Ean13 code has to have a length of 13 characters.')
        return False

    sum = 0
    ean_len = int(len(eancode))
    for i in range(ean_len-1):
        pos = int(ean_len-2-i)
        if is_pair(i):
            sum += 3 * int(eancode[pos])
        else:
            sum += int(eancode[pos])
    check = 10 - operator.mod(sum, 10)
    if check == 10:
        check = 0

    return check == int(eancode[-1])


def check_ean11(eancode):
    pass

def check_gtin14(eancode):
    pass

def check_code128(eancode):
    return True

DICT_CHECK_EAN = {8: check_ean8,
                  11: check_ean11,
                  12: check_upc,
                  13: check_ean13,
                  14: check_gtin14,
                  128: check_code128,
                  }


def check_ean(eancode):
    #_logger.info("Len %s:%s" % (len(eancode), DICT_CHECK_EAN[128](eancode)))
    #eancode = eancode.rstrip()
    if not eancode:
        return True
    if not len(eancode) in DICT_CHECK_EAN:
        if len(eancode) > 128:
            return False
        else:
            return DICT_CHECK_EAN[128](eancode)
    try:
        int(eancode)
    except:
        return False
    return DICT_CHECK_EAN[len(eancode)](eancode)


class ProductEan13(models.Model):
    _name = 'product.ean13'
    _description = "List of barcodes as EAN13, code18, GS1 for a product."
    _order = 'sequence, id'

    name = fields.Char(string='UCC/EAN13/GS1', size=14, required=True)
    sequence = fields.Integer(string='Sequence', default=0)
    type = fields.Char(string='Barcode type', size=10, required=True)
    product_id = fields.Many2one(
        string='Product', comodel_name='product.product', required=True)

    @api.multi
    @api.constrains('name')
    @api.onchange('name')
    def _check_name(self):
        for record in self:
            if not check_ean(self.name):
                raise UserError(
                    _('You provided in row an invalid "Barcode" reference. You '
                        'may use the "Internal Reference" field instead.'))

    @api.multi
    @api.constrains('name')
    def _check_duplicates(self):
        for record in self:
            eans = self.search(
                [('id', '!=', record.id), ('name', '=', record.name)])
            if eans:
                raise UserError(
                    _('The UCC/EAN13/GS1 Barcode "%s" already exists for product '
                      '"%s"') % (record.name, eans[0].product_id.name))


class ProductProduct(models.Model):
    _inherit = 'product.product'

    ean13_ids = fields.One2many(
        comodel_name='product.ean13', inverse_name='product_id',
        string='UCC/EAN13/GS1')
    ean13 = fields.Char(
        string='Main UCC/EAN13/GS1', compute='_compute_ean13', store=True,
        inverse='_inverse_ean13')

    @api.multi
    @api.constrains('ean13')
    def _check_ean_key(self):
        for record in self:
            if not check_ean(record.ean13):
                raise UserError(
                    _('You provided an invalid "Barcode" reference. You '
                        'may use the "Internal Reference" field instead.'))

#        for product in self:
#            try:
#                barcode = get_barcode(product.ean13_ids.search([('name','=',product.name)]), product.name)
#            except ValueError, Argument:
#                raise UserError(
#                        _('You provided an invalid "Barcode" reference. You '
#                          'may use the "Internal Reference" field instead.'))
#            _logger.info("Barcode is %s" % barcode)

    @api.multi
    @api.depends('ean13_ids')
    def _compute_ean13(self):
        for product in self:
            product.ean13 = product.ean13_ids[:1].name

    @api.multi
    def _inverse_ean13(self):
        for product in self:
            if product.ean13_ids:
                product.ean13_ids[:1].write({'name': product.ean13})
            else:
                self.env['product.ean13'].create(self._prepare_ean13_vals())

    @api.multi
    def _prepare_ean13_vals(self):
        self.ensure_one()
        return {
            'product_id': self.id,
            'name': self.ean13,
        }

    @api.model
    def search(self, domain, *args, **kwargs):
        global domain_old
        if filter(lambda x: x[0] == 'ean13', domain):
            #_logger.info("Start Filter %s:%s" % (domain, domain_old))
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
            ean_operator = filter(lambda x: x[0] == 'ean13', domain)[0][1]
            ean_value = filter(lambda x: x[0] == 'ean13', domain)[0][2]
            eans = self.env['product.ean13'].search(
                    [('name', ean_operator, ean_value)])
            domain = filter(lambda x: x[0] != 'ean13', domain)
            #_logger.info("Filter %s" % domain)
            domain_old.append(('ean13_ids', 'in', eans.ids))
            domain += [domain_old[-1]]
            #_logger.info("After Filter %s:%s" % (domain, domain_old))
        return super(ProductProduct, self).search(domain, *args, **kwargs)
