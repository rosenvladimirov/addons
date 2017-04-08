/******************************************************************************
*    Point Of Sale - Pricelist for POS Odoo
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
function pos_loyalty_bg_widgets(instance, module) {
  var _t = instance.web._t;
  var QWeb = instance.web.qweb;

   module.RewardSelectionPopupWidget = module.PopUpWidget.extend({
        template:'RewardSelectionPopupWidget',
        show: function(options){
            options = options || {};
            var self = this;
            this._super(); 
            this.product_list = options.product_list || {};
            this.renderElement();
            this.$(".press_cancel").click(function(){
                var product = options.product_list[0];
                var currentOrder = self.pos.get('selectedOrder');
                product = self.pos.db.get_product_by_id(product.base_product);
                currentOrder.addProduct(product,{'ac_allow':'No'});
                self.pos_widget.screen_selector.set_current_screen('products');
            });
            this.$(".press_ok").click(function(){
                var fields = {}
                var currentOrder = self.pos.get('selectedOrder');
                var product = options.product_list[0];
                var list_ids = [];
                $('.ac_selected_product').each(function(idx,el){
                    if(el.checked){
                        var qty = 1;
                        var input_qty = $(".product_qty"+el.name).val();
                        if(! isNaN(input_qty)){
                            qty = parseFloat(input_qty)
                        }
                        product = self.pos.db.get_product_by_id(parseInt(el.name));
                        currentOrder.addProduct(product,{'ac_allow':'No',price:product.ac_subtotal,quantity:qty});
                        currentOrder.getSelectedLine().set_cross_sell_id(product.base_product);
                        list_ids.push(currentOrder.getSelectedLine().id);
                    }
                });
                product = self.pos.db.get_product_by_id(product.base_product);
                currentOrder.addProduct(product,{'ac_allow':'No'});
                currentOrder.getSelectedLine().child_ids = list_ids;
                self.pos_widget.screen_selector.set_current_screen('products');
            }); 
        },
        get_product_image_url: function(product_id){
            return window.location.origin + '/web/binary/image?model=product.product&field=image_medium&id='+product_id;
        },
  });

  module.LoyaltyButton = module.PosBaseWidget.extend({
        template: 'LoyaltyButton',

        renderElement: function() {
            this._super();
            var self = this;
            this.$el.click(function(){
                var order  = this.pos.get_order();
                var client = order.get_client();
                if (!client) {
                    self.pos_widget.screen_selector.set_current_screen('clientlist');
                }
                var rewards = order.get_available_rewards();
                if (rewards.length === 0) {
                    self.pos.pos_widget.screen_selector.show_popup('error',{
                        message: _t('No Rewards Available'),
                        comment: _t('There are no rewards available for this customer as part of the loyalty program')
                    });
                    return;
                } else if (rewards.length === 1 && this.pos.db.loyalty.rewards.length === 1) {
                    order.apply_reward(rewards[0]);
                    return;
                } else {
                    var list = [];
                    for (var i = 0; i < rewards.length; i++) {
                        list.push({
                            label: rewards[i].name,
                            item:  rewards[i],
                        });
                    }
            this.gui.show_popup('selection',{
                'title': 'Please select a reward',
                'list': list,
                'confirm': function(reward){
                    order.apply_reward(reward);
                },
            });
        }
                return this.pos.db.loyalty && this.pos.db.loyalty.rewards.length;
            });
    },
  });

  module.PosWidget.include({
    build_widgets: function(){
        var self = this;
        this._super();
        this.pos_loyalty_bg_pop = new module.RewardSelectionPopupWidget(this,{});
        this.pos_loyalty_bg_pop.appendTo(this.$el);
        this.pos_loyalty_bg_pop.popup_set['loyalty_button'] = this.pos_loyalty_bg_pop;
        this.pos_loyalty_bg_pop.hide();
        this.pos_loyalty_bg 
        },
  });

  module.OrderWidget.include({
    update_summary: function(){
        this._super();

        var order = this.pos.get_order('selectedOrder');

        var $loypoints = $(this.el).find('.summary .loyalty-points');
        console.log('Find loyalty poin',$(this.el));
        console.log('Find loyalty points find',$loypoints);
        //console.log('Find loyalty points show points',this.pos.db.loyalty);
        if(this.pos.db.loyalty && order.get_client()){
            var points_won      = order.get_won_points();
            var points_spent    = order.get_spent_points();
            var points_total    = order.get_new_total_points();
            console.log('Find loyalty points show points',$(QWeb.render('LoyaltyPoints',{
                widget: this,
                rounding: this.pos.db.loyalty.rounding,
                points_won: points_won,
                points_spent: points_spent,
                points_total: points_total,
            })));

            $loypoints.text($(QWeb.render('LoyaltyPoints',{
                widget: this,
                rounding: this.pos.db.loyalty.rounding,
                points_won: points_won,
                points_spent: points_spent,
                points_total: points_total,
                })));
            //$loypoints = $(this.el).find('.summary .loyalty-points');
            //$loypoints.removeClass('oe_hidden');
            $loypoints.removeClass('oe_hidden');
            console.log('Find loyalty points find after',$loypoints);
            if(points_total < 0){
                //$loypoints.addClass('negative');
                $loypoints.addClass('negative');
            }else{
                $loypoints.removeClass('negative');
            }
        }else{
            $loypoints.empty();
            $loypoints.addClass('oe_hidden');
        }

        if (this.pos.db.loyalty &&
            order.get_client() &&
            this.getParent().action_buttons &&
            this.getParent().action_buttons.loyalty) {

            var rewards = order.get_available_rewards();
            this.getParent().action_buttons.loyalty.highlight(!!rewards.length);
        }
    },
  });
}
