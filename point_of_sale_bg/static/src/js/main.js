openerp.point_of_sale_bg = function(instance) {

    instance.point_of_sale_bg = {};

    var module = instance.point_of_sale_bg;

    openerp_pos_db(instance,module);         // import db.js

    openerp_pos_models(instance,module);     // import pos_models.js

    openerp_pos_basewidget(instance,module); // import pos_basewidget.js

    openerp_pos_keyboard(instance,module);   // import  pos_keyboard_widget.js

    openerp_pos_screens(instance,module);    // import pos_screens.js

    openerp_pos_errors(instance,module);    // import pos_errors.js

    openerp_pos_popups(instance,module);    // import pos_popups.js

    openerp_pos_devices(instance,module);    // import pos_devices.js

    openerp_pos_widgets(instance,module);    // import pos_widgets.js

    instance.web.client_actions.add('pos.ui', 'instance.point_of_sale_bg.PosWidget');
};