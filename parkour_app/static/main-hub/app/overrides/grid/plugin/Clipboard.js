Ext.define('MainHub.overrides.grid.plugin.Clipboard', {
    override: 'Ext.grid.plugin.Clipboard',

    putCellData: function(data, format) {
        var values = Ext.util.TSV.decode(data),
            row,
            recCount = values.length,
            colCount = recCount ? values[0].length : 0,
            sourceRowIdx, sourceColIdx,
            view = this.getCmp().getView(),
            maxRowIdx = view.dataSource.getCount() - 1,
            maxColIdx = view.getVisibleColumnManager().getColumns().length - 1,
            navModel = view.getNavigationModel(),
            destination = navModel.getPosition(),
            dataIndex, destinationStartColumn,
            dataObject = {};

        // If the view is not focused, use the first cell of the selection as the destination.
        if (!destination) {
            view.getSelectionModel().getSelected().eachCell(function(c) {
                destination = c;
                return false;
            });
        }

        if (destination) {
            // Create a new Context based upon the outermost View.
            destination = new Ext.grid.CellContext(view).setPosition(destination.record, destination.column);
        } else {
            destination = new Ext.grid.CellContext(view).setPosition(0, 0);
        }
        destinationStartColumn = destination.colIdx;

        for (sourceRowIdx = 0; sourceRowIdx < recCount; sourceRowIdx++) {
            row = values[sourceRowIdx];

            // Collect new values in dataObject
            for (sourceColIdx = 0; sourceColIdx < colCount; sourceColIdx++) {
                dataIndex = destination.column.dataIndex;

                var destinationColumnEditor = destination.column.config.editor;
                if (destinationColumnEditor) {
                    if (destinationColumnEditor.xtype === 'combobox') {
                        if (dataIndex === 'index_i7' || dataIndex === 'index_i5') {
                            var indexType = destination.record.get('index_type');
                            var indexReads = destination.record.get('index_reads');

                            if (indexType !== 1) { break; }  // Index Type != 'Other'

                            if ((indexReads === 1 && dataIndex !== 'index_i7') ||
                                (indexReads === 2 && dataIndex !== 'index_i7' && dataIndex !== 'index_i5')) {
                                break;  // Don't allow pasting into combobox fields except for Index I7/I5
                            }
                        } else if (dataIndex === 'rna_quality' || dataIndex === 'rna_quality_facility') {
                            var nucleicAcidType = destination.record.get('nucleic_acid_type');

                            if (!nucleicAcidType) { break; }  // NAT is not set

                            var nucleicAcidTypeRecord = Ext.getStore('nucleicAcidTypesStore').findRecord(
                                'id', nucleicAcidType
                            );

                            if (!nucleicAcidTypeRecord ||
                                (nucleicAcidTypeRecord && nucleicAcidTypeRecord.get('type') === 'DNA')) {
                                break;  // NAT is not RNA
                            }
                        } else {
                            break;  // // Don't allow pasting into combobox fields
                        }
                    }
                } else {
                    break;  // Don't allow pasting into read-only fields
                }

                if (dataIndex) {
                    switch (format) {
                        // Raw field values
                        case 'raw':
                            dataObject[dataIndex] = row[sourceColIdx];
                            break;

                        // Textual data with HTML tags stripped
                        case 'text':
                            dataObject[dataIndex] = row[sourceColIdx];
                            break;

                        // innerHTML from the cell inner
                        case 'html':
                            break;
                    }
                }
                // If we are at the end of the destination row, break the column loop.
                if (destination.colIdx === maxColIdx) {
                    break;
                }
                destination.setColumn(destination.colIdx + 1);
            }

            // Update the record in one go.
            destination.record.set(dataObject);
            dataObject = {};

            // If we are at the end of the destination store, break the row loop.
            if (destination.rowIdx === maxRowIdx) {
                break;
            }

            // Jump to next row in destination
            destination.setPosition(destination.rowIdx + 1, destinationStartColumn);
        }

        // BatchAdd: Trigger grid validation after pasting
        if (this.cmp.id === 'batchAddGrid') {
            this.cmp.fireEvent('validate');
        }
    }
});
