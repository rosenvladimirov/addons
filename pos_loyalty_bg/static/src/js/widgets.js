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

    module.RewardCategoriesWidget = module.PosBaseWidget.extend({
        template: 'RewardCategoriesWidget',

        init: function(parent, options){
            var self = this;
            this._super(parent,options);
            this.product_type = options.product_type || 'all';  // 'all' | 'weightable'
            this.onlyWeightable = options.onlyWeightable || false;
            this.curr_id = 0;
            this.breadcrumb = [];
            this.rewards = options.rewards || {};
            this.product_list_widget = options.product_list_widget || null;
            this.reward_cache = new module.DomCache();
            this.set_rewards();

            this.switch_rewards_handler = function(event){
                self.set_rewards(self.pos.db.get_reward_by_id(Number(this.dataset['rewardId'])));
                self.renderElement();
            };
        },

        // changes the category. if undefined, sets to root category
        set_rewards : function(rewards){
            var db = this.pos.db;
            if(!rewards){
                this.rewards = db.get_reward_by_id(0);
            }else{
                this.rewards = rewards;
            }
            this.breadcrumb = [];
            var ancestors_ids = db.get_reward_ancestors_ids(this.rewards.id);
            for(var i = 1; i < ancestors_ids.length; i++){
                this.breadcrumb.push(db.get_reward_by_id(ancestors_ids[i]));
            }
        },

        get_image_url: function(category){
            return window.location.origin + '/web/binary/image?model=pos.reward&field=image_medium&id='+category.id;
        },

        render_reward: function( reward, with_image ){
            var cached = this.reward_cache.get_node(reward.id);
            if(!cached){
                if(with_image){
                    var image_url = this.get_image_url(reward);
                    var reward_html = QWeb.render('RewardButton',{ 
                            widget:  this, 
                            reward: reward, 
                            image_url: this.get_image_url(reward),
                        });
                        reward_html = _.str.trim(category_html);
                    var reward_node = document.createElement('div');
                        reward_node.innerHTML = reward_html;
                        reward_node = reward_node.childNodes[0];
                }else{
                    var reward_html = QWeb.render('RewardSimpleButton',{ 
                            widget:  this, 
                            reward: reward, 
                        });
                        reward_html = _.str.trim(reward_html);
                    var reward_node = document.createElement('div');
                        reward_node.innerHTML = reward_html;
                        reward_node = reward_node.childNodes[0];
                }
                this.reward_cache.cache_node(reward.id,reward_node);
                return reward_node;
            }
            return cached;
        },

        replace: function($target){
            this.renderElement();
            var target = $target[0];
            target.parentNode.replaceChild(this.el,target);
        },

        renderElement: function(){
            var self = this;

            var el_str  = openerp.qweb.render(this.template, {widget: this});
            var el_node = document.createElement('div');
                el_node.innerHTML = el_str;
                el_node = el_node.childNodes[1];

            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }

            this.el = el_node;

            var hasimages = false;  //if none of the subcategories have images, we don't display buttons with icons
            var list_container = el_node.querySelector('.category-list');
            if (list_container) { 
                if (!hasimages) {
                    list_container.classList.add('simple');
                } else {
                    list_container.classList.remove('simple');
                }
            }

            var buttons = el_node.querySelectorAll('.js-category-switch');
            for(var i = 0; i < buttons.length; i++){
                buttons[i].addEventListener('click',this.switch_rewards_handler);
            }

            var products = this.pos.db.get_product_by_reward(this.rewards.id);
            this.product_list_widget.set_product_list(products);
        },

        // resets the current category to the root category
        reset_reward: function(){
            this.set_rewards();
            this.renderElement();
        },
  });

  module.RewardsSelectionPopupWidget = module.PopUpWidget.extend({
        template:'RewardsSelectionPopupWidget',
        init: function(parent){
            var self = this;
            this._super();
            console.log("PopUp this", this);
            console.log("PopUp self", self);
            console.log("PopUp parent", parent);
            this.product_screen = new module.RewardProductScreenWidget(parent,{});
            this.product_screen.appendTo(self.$('.placeholder-ProductScreenWidget'));
        },
        show: function(options){
            var self = this;
            this._super(options);
            this.renderElement();
        },
  });

  module.PosWidget.include({
        build_widgets: function(){
            var self = this;
            this._super();
            this.reward_select = new module.RewardsSelectionPopupWidget(this);
            console.log("PopUp this", this);
            console.log("PopUp self", self);
            console.log("build widget", this.reward_select);
            //this.reward_select.init(this,{rewards: this.pos.db.get_reward_by_id(0), products: this.pos.db.get_product_by_allreward()});
            this.reward_select.appendTo(this.$el);
            this.screen_selector.popup_set['reward_select'] = this.reward_select;
            this.reward_select.hide();
        },
    });

  module.LoyaltyButtonWidget = module.PosBaseWidget.extend({
        template: 'LoyaltyButton',

        renderElement: function() {
            this._super();
            var self = this;
            this.$el.click(function(){
                var order  = self.pos.get_order();
                var client = order.get_client();
                var db = self.pos.db;
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
                } else if (rewards.length === 1 && self.pos.db.loyalty.rewards.length === 1) {
                    order.apply_reward(rewards[0]);
                    return;
                } else {
                    console.log("Button", self);
                    console.log("select", self.pos.pos_widget.screen_selector.popup_set['reward_select']);
                    self.pos.pos_widget.screen_selector.popup_set['reward_select'].start(self,{rewards: rewards, products: db.get_product_by_allreward()});
                }
                return self.pos.db.loyalty && self.pos.db.loyalty.rewards.length;
            });
        },
  });

  module.PosWidget = module.PosWidget.extend({
          build_widgets: function(){
              this._super();
            // Add buttons
              this.LoyaltyButton = new module.LoyaltyButtonWidget(this,{});
              this.LoyaltyButton.appendTo(this.pos_widget.$('.control-buttons'));
              this.pos_widget.$('.control-buttons').removeClass('oe_hidden');
          },
  });

  module.OrderWidget.include({
    update_summary: function(){
        this._super();

        var order = this.pos.get_order('selectedOrder');

        var $loypoints = $(this.el).find('.div-loyalty-points');
        //console.log('Find loyalty poin',$(this.el));
        //console.log('Find loyalty points find',$loypoints);
        //console.log('Find loyalty points show points',this.pos.db.loyalty);
        if(this.pos.db.loyalty && order.get_client()){
            var points_won      = order.get_won_points();
            var points_spent    = order.get_spent_points();
            var points_total    = order.get_new_total_points();
            //console.log('Find loyalty points show points',$(QWeb.render('LoyaltyPoints',{
            //    widget: this,
            //    rounding: this.pos.db.loyalty.rounding,
            //    points_won: points_won,
            //    points_spent: points_spent,
            //    points_total: points_total,
            //})));

            $loypoints.html($(QWeb.render('LoyaltyPoints',{
                widget: this,
                rounding: this.pos.db.loyalty.rounding,
                points_won: points_won,
                points_spent: points_spent,
                points_total: points_total,
                })));
            //$loypoints = $(this.el).find('.summary .loyalty-points');
            //$loypoints.removeClass('oe_hidden');
            $loypoints.removeClass('oe_hidden');
            //console.log('Find loyalty points find after',$loypoints);
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
            this.getParent().LoyaltyButton) {
            //console.log('Button', this.getParent().LoyaltyButton)
            var rewards = order.get_available_rewards();
            $(this.pos_widget.el).find('.rewards-button').removeClass('oe_hidden');
        } else {
            $(this.pos_widget.el).find('.rewards-button').addClass('oe_hidden');
            //this.getParent().LoyaltyButton.highlight(!!rewards.length);
        }
    },
  });
}
