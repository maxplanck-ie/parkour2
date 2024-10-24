/**
 * @private
 */
Ext.define("Ext.dataview.element.Container", {
  extend: "Ext.Component",

  /**
   * @event itemtouchstart
   * Fires whenever an item is touched
   * @param {Ext.dataview.element.Container} this
   * @param {Ext.dom.Element} item The item touched
   * @param {Number} index The index of the item touched
   * @param {Ext.event.Event} e The event object
   */

  /**
   * @event itemtouchmove
   * Fires whenever an item is moved
   * @param {Ext.dataview.element.Container} this
   * @param {Ext.dom.Element} item The item moved
   * @param {Number} index The index of the item moved
   * @param {Ext.event.Event} e The event object
   */

  /**
   * @event itemtouchend
   * Fires whenever an item is touched
   * @param {Ext.dataview.element.Container} this
   * @param {Ext.dom.Element} item The item touched
   * @param {Number} index The index of the item touched
   * @param {Ext.event.Event} e The event object
   */

  /**
   * @event itemtap
   * Fires whenever an item is tapped
   * @param {Ext.dataview.element.Container} this
   * @param {Ext.dom.Element} item The item tapped
   * @param {Number} index The index of the item tapped
   * @param {Ext.event.Event} e The event object
   */

  /**
   * @event itemtaphold
   * Fires whenever an item is tapped
   * @param {Ext.dataview.element.Container} this
   * @param {Ext.dom.Element} item The item tapped
   * @param {Number} index The index of the item tapped
   * @param {Ext.event.Event} e The event object
   */

  /**
   * @event itemsingletap
   * Fires whenever an item is singletapped
   * @param {Ext.dataview.element.Container} this
   * @param {Ext.dom.Element} item The item singletapped
   * @param {Number} index The index of the item singletapped
   * @param {Ext.event.Event} e The event object
   */

  /**
   * @event itemdoubletap
   * Fires whenever an item is doubletapped
   * @param {Ext.dataview.element.Container} this
   * @param {Ext.dom.Element} item The item doubletapped
   * @param {Number} index The index of the item doubletapped
   * @param {Ext.event.Event} e The event object
   */

  /**
   * @event itemswipe
   * Fires whenever an item is swiped
   * @param {Ext.dataview.element.Container} this
   * @param {Ext.dom.Element} item The item swiped
   * @param {Number} index The index of the item swiped
   * @param {Ext.event.Event} e The event object
   */

  /**
   * @event mouseover
   * Fires whenever the a mouseover event is received on an item
   * @param {Ext.dataview.element.Container} this
   * @param {Ext.dom.Element} item The item
   * @param {Number} index The index of the item
   * @param {Ext.event.Event} e The event object
   */

  /**
   * @event mouseout
   * Fires whenever a mouseout event is received on an item
   * @param {Ext.dataview.element.Container} this
   * @param {Ext.dom.Element} item The item
   * @param {Number} index The index of the item
   * @param {Ext.event.Event} e The event object
   */

  classCls: Ext.baseCSSPrefix + "dataview-container",

  itemSelector: "." + Ext.baseCSSPrefix + "dataview-container > div",

  doInitialize: function () {
    this.element.on({
      touchstart: "onItemTouchStart",
      touchend: "onItemTouchEnd",
      tap: "onItemTap",
      taphold: "onItemTapHold",
      touchmove: "onItemTouchMove",
      singletap: "onItemSingleTap",
      doubletap: "onItemDoubleTap",
      swipe: "onItemSwipe",
      mouseover: "onItemMouseOver",
      mouseout: "onItemMouseOut",
      delegate: "> div",
      scope: this
    });
  },

  /**
   * @private
   */
  initialize: function () {
    this.callParent();
    this.doInitialize();
  },

  onItemTouchStart: function (e) {
    var me = this,
      target = e.currentTarget,
      index = me.getViewItems().indexOf(target);

    Ext.get(target).on({
      touchmove: "onItemTouchMove",
      scope: me,
      single: true
    });

    me.fireEvent("itemtouchstart", me, Ext.get(target), index, e);
  },

  onItemTouchEnd: function (e) {
    var me = this,
      target = e.currentTarget,
      index = me.getViewItems().indexOf(target);

    Ext.get(target).un({
      touchmove: "onItemTouchMove",
      scope: me
    });

    me.fireEvent("itemtouchend", me, Ext.get(target), index, e);
  },

  onItemTouchMove: function (e) {
    var me = this,
      target = e.currentTarget,
      index = me.getViewItems().indexOf(target);

    me.fireEvent("itemtouchmove", me, Ext.get(target), index, e);
  },

  onItemTap: function (e) {
    var me = this,
      target = e.currentTarget,
      index = me.getViewItems().indexOf(target);

    me.fireEvent("itemtap", me, Ext.get(target), index, e);
  },

  onItemTapHold: function (e) {
    var me = this,
      target = e.currentTarget,
      index = me.getViewItems().indexOf(target);

    me.fireEvent("itemtaphold", me, Ext.get(target), index, e);
  },

  onItemDoubleTap: function (e) {
    var me = this,
      target = e.currentTarget,
      index = me.getViewItems().indexOf(target);

    me.fireEvent("itemdoubletap", me, Ext.get(target), index, e);
  },

  onItemSingleTap: function (e) {
    var me = this,
      target = e.currentTarget,
      index = me.getViewItems().indexOf(target);

    me.fireEvent("itemsingletap", me, Ext.get(target), index, e);
  },

  onItemSwipe: function (e) {
    var me = this,
      target = e.currentTarget,
      index = me.getViewItems().indexOf(target);

    me.fireEvent("itemswipe", me, Ext.get(target), index, e);
  },

  onItemMouseOver: function (e) {
    var me = this,
      target = e.currentTarget,
      index = me.getViewItems().indexOf(target);

    me.fireEvent("itemmouseover", me, Ext.get(target), index, e);
  },

  onItemMouseOut: function (e) {
    var me = this,
      target = e.currentTarget,
      index = me.getViewItems().indexOf(target);

    me.fireEvent("itemmouseout", me, Ext.get(target), index, e);
  },

  updateListItem: function (record, item) {
    var me = this,
      dataview = me.dataview,
      store = dataview.getStore(),
      index = store.indexOf(record),
      data = dataview.prepareData(record.getData(true), index, record);

    item.innerHTML = this.renderItemTpl(index, data, store);
  },

  addListItem: function (index, record) {
    var me = this,
      dataview = me.dataview,
      store = dataview.getStore(),
      data = dataview.prepareData(record.getData(true), index, record),
      element = me.element,
      childNodes = element.dom.childNodes,
      ln = childNodes.length,
      wrapElement;

    wrapElement = Ext.Element.create(
      this.getItemElementConfig(index, data, store)
    );

    if (!ln || index == ln) {
      wrapElement.appendTo(element);
    } else {
      wrapElement.insertBefore(childNodes[index]);
    }
  },

  getItemElementConfig: function (index, data, store) {
    var dataview = this.dataview,
      itemCls = dataview.getItemCls(),
      cls = dataview.getBaseCls() + "-item";

    if (itemCls) {
      cls += " " + itemCls;
    }

    return {
      cls: cls,
      html: this.renderItemTpl(index, data, store)
    };
  },

  renderItemTpl: function (index, data, store) {
    var dataview = this.dataview,
      itemTpl = dataview.getItemTpl(),
      parent;

    store = store || dataview.getStore();
    parent = store.getData().items;

    data.xcount =
      typeof data.xcount === "number" ? data.xcount : store.getCount();
    data.xindex = typeof data.xindex === "number" ? data.xindex : index;

    return itemTpl.apply(data, parent, index + 1, parent.length);
  },

  doRemoveItemCls: function (cls) {
    var elements = this.getViewItems(),
      ln = elements.length,
      i = 0;

    for (; i < ln; i++) {
      Ext.fly(elements[i]).removeCls(cls);
    }
  },

  doAddItemCls: function (cls) {
    var elements = this.getViewItems(),
      ln = elements.length,
      i = 0;

    for (; i < ln; i++) {
      Ext.fly(elements[i]).addCls(cls);
    }
  },

  // Remove
  moveItemsToCache: function (from, to) {
    var me = this,
      items = me.getViewItems(),
      i = to - from,
      item;

    for (; i >= 0; i--) {
      item = items[from + i];
      Ext.get(item).destroy();
    }
    if (me.getViewItems().length == 0) {
      this.dataview.showEmptyText();
    }
  },

  // Add
  moveItemsFromCache: function (records) {
    var me = this,
      dataview = me.dataview,
      store = dataview.getStore(),
      ln = records.length,
      i,
      record;

    if (ln) {
      dataview.hideEmptyText();
    }

    for (i = 0; i < ln; i++) {
      records[i]._tmpIndex = store.indexOf(records[i]);
    }

    Ext.Array.sort(records, function (record1, record2) {
      return record1._tmpIndex > record2._tmpIndex ? 1 : -1;
    });

    for (i = 0; i < ln; i++) {
      record = records[i];
      me.addListItem(record._tmpIndex, record);
      delete record._tmpIndex;
    }
  },

  // Transform ChildNodes into a proper Array so we can do indexOf...
  getViewItems: function () {
    return Array.prototype.slice.call(this.element.dom.childNodes);
  },

  updateAtNewIndex: function (oldIndex, newIndex, record) {
    this.moveItemsToCache(oldIndex, oldIndex);
    this.moveItemsFromCache([record]);
  },

  doDestroy: function () {
    var elements = this.getViewItems(),
      ln = elements.length,
      i = 0;

    for (; i < ln; i++) {
      Ext.get(elements[i]).destroy();
    }
    this.callParent();
  }
});
