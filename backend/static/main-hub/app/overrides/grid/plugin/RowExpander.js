Ext.define('MainHub.overrides.grid.plugin.RowExpander', {
    override: 'Ext.grid.plugin.RowExpander',

    getHeaderConfig: function() {
        var me = this;
        var lockable = me.grid.lockable && me.grid;

        return {
            width: me.headerWidth,
            ignoreExport: true,
            lockable: false,
            autoLock: true,
            sortable: false,
            resizable: false,
            draggable: false,
            hideable: false,
            menuDisabled: true,
            tdCls: Ext.baseCSSPrefix + 'grid-cell-special',
            innerCls: Ext.baseCSSPrefix + 'grid-cell-inner-row-expander',
            renderer: function(v, p, record) {
                var files = record.get('files');
                if (files && files.length === 0) {
                    return '&#160;';
                } else {
                    return '<span data-qtip="Click to show attached files" class="request-attachments-expander">' +
                        '<i class="fa fa-paperclip" aria-hidden="true"></i></span>';
                }
            },
            processEvent: function(type, view, cell, rowIndex, cellIndex, e, record) {
                var isTouch = e.pointerType === 'touch';
                var isExpanderClick = !!e.getTarget('.request-attachments-expander');

                if ((type === 'click' && isExpanderClick) || (type === 'keydown' && e.getKey() === e.SPACE)) {

                    // Focus the cell on real touch tap.
                    // This is because the toggleRow saves and restores focus
                    // which may be elsewhere than clicked on causing a scroll jump.
                    if (isTouch) {
                        cell.focus();
                    }
                    me.toggleRow(rowIndex, record, e);
                    e.stopSelection = !me.selectRowOnExpand;
                } else if (e.type === 'mousedown' && !isTouch && isExpanderClick) {
                    e.preventDefault();
                }
            },

            // This column always migrates to the locked side if the locked side is visible.
            // It has to report this correctly so that editors can position things correctly
            isLocked: function() {
                return lockable && (lockable.lockedGrid.isVisible() || this.locked);
            },

            // In an editor, this shows nothing.
            editRenderer: function() {
                return '&#160;';
            }
        };
    }
});
