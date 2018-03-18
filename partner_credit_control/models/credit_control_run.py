# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import time

from openerp import models, fields, api, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt

_logger = logging.getLogger('credit.line.control')

class CreditControlRun(models.Model):
    _inherit = "credit.control.run"

    last_date = fields.Datetime(string='Controlling date',
                                 default=lambda *a: time.strftime(dt))

    @api.model
    def create(self, vals):
        if not vals.get('last_date', False):
            partner_obj = self.env['res.partner']
            vals['last_date'] = time.strftime(dt)
            partner = partner_obj.search([('last_credit_control_date', '!=', vals['last_date'])])
            _logger.info("Vals %s:%s" % (vals,partner))
            if partner:
                partner.write({'last_credit_control_date': vals['last_date']})
        return super(CreditControlRun, self).create(vals)
