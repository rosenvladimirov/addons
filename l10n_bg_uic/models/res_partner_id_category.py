# -*- coding: utf-8 -*-
#
# © 2004-2010 Tiny SPRL http://tiny.be
# © 2010-2012 ChriCar Beteiligungs- und Beratungs- GmbH
#             http://www.camptocamp.at
# © 2015 Antiun Ingenieria, SL (Madrid, Spain)
#        http://www.antiun.com
#        Antonio Espinosa <antonioea@antiun.com>
# ©  2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import api, models, fields
from openerp.exceptions import ValidationError, Warning as UserError
from openerp.tools.safe_eval import safe_eval
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class ResPartnerIdCategory(models.Model):
    _inherit = "res.partner.id_category"

    def _get_fieldname(self):
        selection = super(ResPartnerIdCategory, self)._get_fieldname()
        _logger.info("Get selection %s" % selection)
        #_logger.war("Test")
        if not selection:
            selection = []
        selection.append(
            ('uic', 'Inditification code for Tax administration registrations'),
            )
        return selection

    fieldname = fields.Selection(
        _get_fieldname,
        'Choice field name to fill', default='vat')

    def _default_fld(self):
        res = super(ResPartnerIdCategory, self)._default_fld()
        res.update({'uic': {'code': 'bg_uic', 'name': 'UIC number Taxadmin agency in Bulgaria', 'active': True, 'validation_model': 'bg.vat', 'validation_model_base': 'bg.vat', 'fieldname': 'uic'}})
        return res

