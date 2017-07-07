/******************************************************************************
*    Point Of Sale - Fiscal Printer Datecs for POS Odoo
*    @author Rosen Vladimirov <vladimirov.rosen@gmail.com>
*
*    This program is free software: you can redistribute it and/or modify
*    it under the terms of the GNU Affero General Public License as
*    published by the Free Software Foundation, either version 3 of the
*    License, or (at your option) any later version.
*    This program is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU Affero General Public License for more details.
*    You should have received a copy of the GNU Affero General Public License
*    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*
******************************************************************************/

function pos_datecs_models(instance, module) {
    var _t = instance.web._t;
    var round_pr = instance.web.round_precision;
    var round_di = instance.web.round_decimals;

    var _super_PosModel = module.PosModel;
    module.PosModel = module.PosModel.extend({
        initialize: function(session, attributes) {
            _super_PosModel.prototype.initialize.apply(this, arguments);

            var pos_config_model = _.find(_super_PosModel.prototype.models,function(model){ return model.model === 'pos.config'; });
            var pos_config_model_inx = _super_PosModel.prototype.models.findIndex(function(model){ return model.model === 'pos.config'; });
            //pos_config_model.fields.push('iface_fprint_via_proxy');
            console.log("Datecs", pos_config_model);
            console.log("Datecs index", pos_config_model_inx)
        },
    });
}