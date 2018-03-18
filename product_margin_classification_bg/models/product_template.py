# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import api, models, fields, exceptions, tools, _
import openerp.addons.decimal_precision as dp
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    MARGIN_STATE_SELECTION = [
        ('new', 'New Price'),
        ('ok', 'Correct Margin'),
        ('cheap', 'Cheaper'),
        ('expensive', 'Too Expensive'),
    ]

    # Columns Section
    margin_classification_id = fields.Many2one(
        comodel_name='product.margin.classification',
        string='Margin Classification')

    theoretical_price = fields.Float(
        string='Theoretical Price', store=True,
        digits=dp.get_precision('Product Price'),
        compute='_compute_theoretical_multi', multi='theoretical_multi')

    theoretical_price_vat = fields.Float(
        string='Theoretical Price with VAT', store=False,
        digits=dp.get_precision('Product Price'),
        compute='_compute_theoretical_multi_vat', multi='theoretical_multi')

    theoretical_difference = fields.Float(
        string='Theoretical Difference', store=True,
        digits=dp.get_precision('Product Price'),
        compute='_compute_theoretical_multi', multi='theoretical_multi')

    margin_state = fields.Selection(
        string='Theoretical Price State', store=True,
        selection=MARGIN_STATE_SELECTION,
        compute='_compute_theoretical_multi', multi='theoretical_multi')

    # Compute Section for vat price
    @api.multi
    @api.depends(
        'standard_price', 'list_price')
    def _compute_theoretical_multi_vat(self):
        for template in self:
            template.theoretical_price_vat = template.taxes_id.compute_all(template.theoretical_price, 1, inverce=True)['total_included']

    # Compute Section
    @api.multi
    @api.depends(
        'standard_price', 'list_price',
        'margin_classification_id.margin',
        'margin_classification_id.price_round',
        'margin_classification_id.price_surcharge')
    def _compute_theoretical_multi(self):
        for template in self:
            classification = template.margin_classification_id
            if classification:
                multi = 1 + (classification.margin / 100)
                temp_vat = template.taxes_id.compute_all(template.standard_price * multi, 1, inverce=False)['total_included']
                temp_price = tools.float_round(
                    temp_vat,
                    precision_rounding=classification.price_round) +\
                    classification.price_surcharge
                _logger.info("New price with VAT %s:%s:%s:%s" % (multi,template.standard_price,temp_price,temp_vat))
            else:
                temp_price = template.taxes_id.compute_all(template.list_price, 1, inverce=False)['total_included']
            difference = (template.list_price - template.taxes_id.compute_all(temp_price, 1, inverce=True)['total_included'])
            if max(difference, -difference) < 10 ** -2:
                difference = 0
            template.theoretical_difference = difference
            if difference < 0:
                template.margin_state = 'cheap'
            elif difference > 0:
                template.margin_state = 'expensive'
            else:
                template.margin_state = 'ok'
            template.theoretical_price = temp_price

    # Custom Section
    @api.multi
    def use_theoretical_price(self):
        for template in self:
            template.list_price = template.taxes_id.compute_all(template.theoretical_price, 1, inverce=True)['total_included']

    @api.multi
    def recalculate_theoretical_price(self):
        for template in self:
            template._compute_theoretical_multi()
