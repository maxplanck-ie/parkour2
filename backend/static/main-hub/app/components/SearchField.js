Ext.define('MainHub.components.SearchField', {
  extend: 'Ext.form.field.Text',

  alias: 'widget.parkoursearchfield',

  triggers: {
    clear: {
      weight: 0,
      cls: Ext.baseCSSPrefix + 'form-clear-trigger',
      hidden: true,
      handler: 'onClearClick',
      scope: 'this'
    },
    search: {
      weight: 1,
      cls: Ext.baseCSSPrefix + 'form-search-trigger',
      handler: 'onSearchClick',
      scope: 'this'
    }
  },

  initComponent: function () {
    var me = this;
    var store = me.store;

    me.callParent(arguments);
    me.on('specialkey', function (f, e) {
      if (e.getKey() === e.ENTER) {
        me.onSearchClick();
      }
    });

    if (!store || !store.isStore) {
      store = me.store = Ext.data.StoreManager.lookup(store);
    }
  },

  onClearClick: function () {
    var me = this;
    var activeFilter = me.activeFilter;

    if (activeFilter) {
      me.setValue('');
      me.store.getFilters().remove(activeFilter);
      me.activeFilter = null;
      me.getTrigger('clear').hide();
      me.updateLayout();
    }
  },

  onSearchClick: function () {
    var me = this;
    var query = me.getValue();
    var filters = me.store.getFilters();
    var dataIndices = Ext.Array.pluck(me.store.model.fields, 'name');

    if (query.length > 0) {
      var prevFilter = me.activeFilter;
      if (prevFilter) {
        filters.remove(prevFilter);
      }

      me.activeFilter = new Ext.util.Filter({
        filterFn: function (item) {
          var contains = false;
          Ext.each(dataIndices, function (dataIndex) {
            var value = item.get(dataIndex);
            if (value && value.toString().toLowerCase().indexOf(query.toLowerCase()) > -1) {
              contains = contains || true;
            }
          });
          return contains;
        }
      });

      filters.add(me.activeFilter);
      me.getTrigger('clear').show();
      me.updateLayout();
    } else {
      me.onClearClick();
    }
  }
});
