/******************************************************************************
*    Point Of Sale - Fiscal Printers Datecs for POS Odoo
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
function pos_datecs_widgets(instance, module) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;

    // this is used to notify the user if the pos is connected to the proxy
    module.ProxyStatusWidget = module.StatusWidget.extend({
        template: 'ProxyStatusWidget',
        set_smart_status: function(status){
            //Block error message from status
            var iface_print_via_proxy = this.pos.config.iface_print_via_proxy;
            this.pos.config.iface_print_via_proxy = False;
            this._super(status);
            this.pos.config.iface_print_via_proxy = iface_print_via_proxy
            if(status.status === 'connected'){
                var warning = false;
                var msg = ''
                if( this.pos.config.iface_fprint_via_proxy ) {
                    var printer = status.drivers.fprint ? status.drivers.fprint.status : false;
                    if( printer != 'connected' && printer != 'connecting'){
                        warning = true;
                        msg = msg ? msg + ' & ' : msg;
                        msg += _t('Printer');
                    }
                }
                msg = msg ? msg + ' ' + _t('Offline') : msg;
                this.set_status(warning ? 'warning' : 'connected', msg);
            }
        },
    });
}
