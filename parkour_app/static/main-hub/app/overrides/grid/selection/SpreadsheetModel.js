Ext.define('MainHub.overrides.grid.selection.SpreadsheetModel', {
    override: 'Ext.grid.selection.SpreadsheetModel',

    selectByPosition: function(pos) {
        return this.selectCells(pos, pos);
    },

    privates: {
        getNumbererColumnConfig: function() {
            var me = this;

            return {
                xtype: 'rownumberer',
                width: me.rowNumbererHeaderWidth,
                tdCls: me.rowNumbererTdCls,
                cls: me.rowNumbererHeaderCls,
                locked: me.hasLockedHeader
            };
        }
    }
});
