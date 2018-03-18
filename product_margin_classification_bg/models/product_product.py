# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import api, models, fields, exceptions, tools, _
import openerp.addons.decimal_precision as dp
_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    MARGIN_STATE_SELECTION = [
        ('new', 'New Price'),
        ('ok', 'Correct Margin'),
        ('cheap', 'Cheaper'),
        ('expensive', 'Too Expensive'),
    ]

    margin_state = fields.Selection(related="product_tmpl_id.margin_state", strin="Theoretical Price State")
