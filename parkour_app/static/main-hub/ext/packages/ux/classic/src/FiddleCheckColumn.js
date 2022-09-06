Ext.define('Ext.ux.FiddleCheckColumn', {
    extend: 'Ext.grid.column.CheckColumn',
    alias: 'widget.fiddlecheckcolumn',

    renderTpl: [
        '<div id="{id}-titleEl" data-ref="titleEl" {tipMarkup}class="', Ext.baseCSSPrefix, 'column-header-inner<tpl if="!$comp.isContainer"> ', Ext.baseCSSPrefix, 'leaf-column-header</tpl>',
            '<tpl if="empty"> ', Ext.baseCSSPrefix, 'column-header-inner-empty</tpl>">',
            '<span class="', Ext.baseCSSPrefix, 'column-header-text-container">',
                '<span class="', Ext.baseCSSPrefix, 'column-header-text-wrapper">',
                    '<span id="{id}-textContainerEl" data-ref="textContainerEl" class="', Ext.baseCSSPrefix, 'column-header-text', '{childElCls}">',
                        '<div class="', Ext.baseCSSPrefix, 'grid-checkcolumn" role="button" src="' + Ext.BLANK_IMAGE_URL + '"></div>',
                    '</span>',
                '</span>',
            '</span>',
            '<tpl if="!menuDisabled">',
                '<div id="{id}-triggerEl" data-ref="triggerEl" role="presentation" class="', Ext.baseCSSPrefix, 'column-header-trigger', '{childElCls}" style="{triggerStyle}"></div>',
            '</tpl>',
        '</div>',
        '{%this.renderContainer(out,values)%}'
    ],

    constructor: function(config) {
        var me = this;

        Ext.apply(config, {
            stopSelection: true,
            sortable: false,
            draggable: false,
            resizable: false,
            menuDisabled: true,
            hideable: false,
            tdCls: 'no-tip no-dirty',
            defaultRenderer: me.defaultRenderer,
            checked: false
        });

        me.callParent([config]);

        me.on('headerclick', me.onHeaderClick);
        me.on('selectall', me.onSelectAll);

    },

    /**
     * utility method: given a header component, goes down to the component
     */
    getHeaderCheckboxEl: function(header) {
        return header.getEl().down('.' + Ext.baseCSSPrefix + 'grid-checkcolumn');
    },

    onHeaderClick: function(headerCt, header, e, el) {
        var me = this,
            grid = headerCt.grid,
            checkboxEl = me.getHeaderCheckboxEl(header);

        if (!me.checked) {
            me.fireEvent('selectall', grid.getStore(), header, true);
            checkboxEl.addCls(Ext.baseCSSPrefix + 'grid-checkcolumn-checked');
            me.checked = true;
        } else {
            me.fireEvent('selectall', grid.getStore(), header, false);
            checkboxEl.removeCls(Ext.baseCSSPrefix + 'grid-checkcolumn-checked');
            me.checked = false;
        }
    },

    onSelectAll: function(store, column, checked) {
        var dataIndex = column.dataIndex;
        for (var i = 0; i < store.getCount(); i++) {
            var record = store.getAt(i);
            if (checked) {
                record.set(dataIndex, true);
            } else {
                record.set(dataIndex, false);
            }
        }
    }
});
