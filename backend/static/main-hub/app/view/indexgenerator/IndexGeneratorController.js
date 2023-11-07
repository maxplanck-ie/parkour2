Ext.define('MainHub.view.indexgenerator.IndexGeneratorController', {
  extend: 'MainHub.components.BaseGridController',
  alias: 'controller.index-generator',

  config: {
    control: {
      '#': {
        activate: 'activateView',
        boxready: 'boxready'
      },
      '#index-generator-grid': {
        beforeedit: 'toggleEditors',
        edit: 'editRecord',
        itemcontextmenu: 'showMenu',
        groupcontextmenu: 'showGroupMenu'
      },
      '#check-column': {
        beforecheckchange: 'beforeSelect',
        checkchange: 'checkRecord'
      },
      '#save-pool-button': {
        click: 'save'
      },
      '#generate-indices-button': {
        click: 'generateIndices'
      }
    }
  },

  activateView: function (view) {
    var store = view.down('grid').getStore();
    Ext.getStore(store.getId()).reload();
    Ext.getCmp('poolSizeCb').clearValue();  // reset PoolSize
  },

  boxready: function () {
    Ext.getStore('IndexGenerator').on('load', function () {
      Ext.getCmp('pool-grid').getStore().removeAll();
    });
  },

  toggleEditors: function (editor, context) {
    var record = context.record;
    var indexTypeEditor = Ext.getCmp('indexTypePoolingEditor');

    // Don't show the editors when a selection checkbox was clicked
    if (context.colIdx === 0) {
      return false;
    }

    if (record.get('record_type') === 'Library') {
      indexTypeEditor.disable();
    } else {
      indexTypeEditor.enable();
    }
  },

  beforeSelect: function () {
    if (!Ext.getCmp('poolSizeCb').getValue()) {
      new Noty({
        text: 'Pool Size must be set.',
        type: 'warning'
      }).show();
      return false;
    }
  },

  editRecord: function (editor, context) {
    var store = editor.grid.getStore();
    this.syncStore(store.getId());
  },

  applyToAll: function (gridView, record, dataIndex) {
    var self = this;
    var store = gridView.grid.getStore();
    var allowedColumns = ['read_length', 'index_type'];

    if (dataIndex && allowedColumns.indexOf(dataIndex) !== -1) {
      store.each(function (item) {
        if (
          item.get(store.groupField) === record.get(store.groupField) &&
          item !== record
        ) {
          if (
            dataIndex === 'read_length' ||
            (dataIndex === 'index_type' && item.get('record_type') === 'Sample')
          ) {
            item.set(dataIndex, record.get(dataIndex));
          }
        }
      });

      self.syncStore(store.getId());
    } else {
      self._showEditableColumnsMessage(gridView, allowedColumns);
    }
  },

  // showContextMenu: function (gridView, record, item, index, e) {
  //   var me = this;
  //   e.stopEvent();
  //   Ext.create('Ext.menu.Menu', {
  //     items: [
  //       {
  //         text: 'Apply to All',
  //         iconCls: 'x-fa fa-check-circle',
  //         handler: function () {
  //           var dataIndex = MainHub.Utilities.getDataIndex(e, gridView);
  //           me.applyToAll(record, dataIndex);
  //         }
  //       }
  //       // {
  //       //   text: 'Reset',
  //       //   iconCls: 'x-fa fa-eraser',
  //       //   handler: function () {
  //       //     Ext.Msg.show({
  //       //       title: 'Reset',
  //       //       message: 'Are you sure you want to reset the record\'s values?',
  //       //       buttons: Ext.Msg.YESNO,
  //       //       icon: Ext.Msg.QUESTION,
  //       //       fn: function (btn) {
  //       //         if (btn === 'yes') {
  //       //           me.reset(record);
  //       //         }
  //       //       }
  //       //     });
  //       //   }
  //       // }
  //     ]
  //   }).showAt(e.getXY());
  // },

  selectUnselectAll: function (grid, groupId, selected) {
    var indexGeneratorStore = grid.getStore();
    var poolGridStore = Ext.getCmp('pool-grid').getStore();
    var checkColumn = grid.down('#check-column');
    var selectedRecord;

    // Unselect all
    if (!selected) {
      indexGeneratorStore.each(function (record) {
        if (record.get(indexGeneratorStore.groupField) === groupId) {
          var pooledRecordIdx = poolGridStore.findBy(function (item) {
            return item.get('pk') === record.get('pk') &&
              item.get('record_type') === record.get('record_type');
          });
          if (pooledRecordIdx !== -1) {
            poolGridStore.removeAt(pooledRecordIdx);
          }
          record.set('selected', false);
        }
      });
      return false;
    }

    if (!Ext.getCmp('poolSizeCb').getValue()) {
      new Noty({
        text: 'Pool Size must be set.',
        type: 'warning'
      }).show();
      return false;
    }

    indexGeneratorStore.each(function (item) {
      var itemInPoolIdx = poolGridStore.findBy(function (rec) {
        return rec.get('record_type') === item.get('record_type') &&
          rec.get('pk') === item.get('pk');
      });

      if (item.get(indexGeneratorStore.groupField) === groupId && itemInPoolIdx === -1) {
        selectedRecord = item;
        checkColumn.fireEvent('checkchange', checkColumn, null, true, item, null, {
          multipleSelect: true
        });
      }
    });

    // Show notification
    if (selectedRecord) {
      this._isPoolSizeOk(poolGridStore, selectedRecord);
    }
  },

  checkRecord: function (checkColumn, rowIndex, checked, record, e, eOpts) {
    var grid = Ext.getCmp('pool-grid');
    var store = grid.getStore();
    var multipleSelect = false;
    var startCoordinate = grid.down('#start-coordinate');
    var direction = grid.down('#direction');

    if (eOpts && eOpts.hasOwnProperty('multipleSelect')) {
      multipleSelect = eOpts.multipleSelect;
    }

    // Reset all samples' indices
    this._resetGeneratedIndices();

    if (checked) {
      if (
        this._isIndexTypeSet(store, record) &&
        // this._isUnique(store, record) &&
        this._isCompatible(store, record) &&
        this._isPoolSizeOk(store, record, multipleSelect)
      ) {
        record.set('selected', true);

        var indexI7 = record.get('index_i7');
        var indexI5 = record.get('index_i5');
        var indexI7Sequence = indexI7.split('');
        var indexI5Sequence = indexI5.split('');

        if (indexI7.length === 6) {
          indexI7Sequence = indexI7Sequence.concat([' ', ' ']);
        }

        if (indexI5.length === 0) {
          indexI5Sequence = [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',' ', ' ', ' ', ' '];
        } else if (indexI5Sequence.length === 6) {
          indexI5Sequence = indexI5Sequence.concat([' ', ' ',' ',' ', ' ',' ']);
        }

        var data = {
          pk: record.get('pk'),
          name: record.get('name'),
          record_type: record.get('record_type'),
          sequencing_depth: record.get('sequencing_depth'),
          read_length: record.get('read_length'),
          index_type: record.get('index_type'),
          index_i7_id: record.get('index_i7_id'),
          index_i5_id: record.get('index_i5_id'),
          index_i7: { index: indexI7 },
          index_i5: { index: indexI5 }
        };

        for (var i = 0; i < 12; i++) {
          data['index_i7_' + (i + 1)] = indexI7Sequence[i];
          data['index_i5_' + (i + 1)] = indexI5Sequence[i];
        }

        store.add(data);
      } else {
        record.set('selected', false);
      }
    } else {
      var itemIdx = store.findBy(function (rec) {
        return rec.get('record_type') === record.get('record_type') &&
          rec.get('pk') === record.get('pk');
      });

      if (itemIdx !== -1) {
        store.removeAt(itemIdx);
      }
    }

    // Update Summary
    grid.getView().refresh();

    // Update grid's header and enable/disable 'Pool' button
    if (store.getCount() > 0) {
      grid.setTitle(Ext.String.format(
        'Pool (total size: {0} M)',
        grid.getStore().sum('sequencing_depth')
      ));
      Ext.getCmp('save-pool-button').enable();

      var recordTypes = Ext.pluck(Ext.Array.pluck(store.data.items, 'data'), 'record_type');
      if (recordTypes.indexOf('Sample') > -1) {
        Ext.getCmp('generate-indices-button').enable();
      }

      // Show plate params
      var indexType = Ext.getStore('IndexTypes').findRecord(
        'id', record.get('index_type'), 0, false, true, true);
      if (indexType && indexType.get('format') === 'plate') {
        startCoordinate.show();
        direction.show();
      }
    } else {
      grid.setTitle('Pool');
      Ext.getCmp('save-pool-button').disable();
      Ext.getCmp('generate-indices-button').disable();
      startCoordinate.hide();
      direction.hide();
    }
  },

  generateIndices: function () {
    var indexGeneratorGrid = Ext.getCmp('index-generator-grid');
    var poolGrid = Ext.getCmp('pool-grid');
    var startCoordinate = poolGrid.down('#start-coordinate');
    var direction = poolGrid.down('#direction');
    var store = poolGrid.getStore();
    var libraries = [];
    var samples = [];

    // Reset all samples' indices
    this._resetGeneratedIndices();

    store.each(function (item) {
      if (item.get('record_type') === 'Library') {
        libraries.push(item.get('pk'));
      } else {
        samples.push(item.get('pk'));
      }
    });

    indexGeneratorGrid.disable();
    poolGrid.setLoading('Generating...');
    Ext.Ajax.request({
      url: 'api/index_generator/generate_indices/',
      method: 'POST',
      timeout: 60000,
      scope: this,
      params: {
        libraries: Ext.JSON.encode(libraries),
        samples: Ext.JSON.encode(samples),
        start_coord: startCoordinate.getValue(),
        direction: direction.getValue()
      },
      success: function (response) {
        var obj = Ext.JSON.decode(response.responseText);
        if (obj.success) {
          store.removeAll();
          store.add(obj.data);
        } else {
          new Noty({ text: obj.error, type: 'error' }).show();
        }

        indexGeneratorGrid.enable();
        poolGrid.setLoading(false);
      },
      failure: function (response) {
        var error = response.statusText;
        try {
          error = Ext.JSON.decode(response.responseText).message;
        } catch (e) {}
        new Noty({ text: error, type: 'error' }).show();
        console.error(response);

        indexGeneratorGrid.enable();
        poolGrid.setLoading(false);
      }
    });
  },

  save: function () {
    var me = this;
    var store = Ext.getCmp('pool-grid').getStore();
    var libraries = [];
    var samples = [];

    if (!this._isPoolValid(store)) {
      new Noty({
        text: 'Some of the indices are empty. The pool cannot be saved.',
        type: 'warning'
      }).show();
      return;
    }

    // if (Ext.query('.problematic-cycle').length > 0) {
    //   var n = new Noty({
    //     text: 'Some of the cycles are non-optimal. Do you want to continue?',
    //     type: 'warning',
    //     timeout: false,
    //     buttons: [
    //       Noty.button('Yes', '', function () {
    //         console.log('button 1 clicked');
    //       }),

    //       Noty.button('No', '', function () {
    //         console.log('button 2 clicked');
    //         n.close();
    //       })
    //     ]
    //   }).show();
    // }

    // Get all libraries' and samples' ids
    store.each(function (record) {
      var item = {
        pk: record.get('pk'),
        index_i7: record.get('index_i7').index,
        index_i5: record.get('index_i5').index
      };
      if (record.get('record_type') === 'Library') {
        libraries.push(item);
      } else {
        samples.push(item);
      }
    });

    Ext.getCmp('poolingContainer').setLoading('Saving...');
    Ext.Ajax.request({
      url: 'api/index_generator/save_pool/',
      method: 'POST',
      scope: this,
      params: {
        pool_size_id: Ext.getCmp('poolSizeCb').getValue(),
        libraries: Ext.JSON.encode(libraries),
        samples: Ext.JSON.encode(samples)
      },
      success: function (response) {
        var obj = Ext.JSON.decode(response.responseText);

        if (obj.success) {
          Ext.getCmp('pool-grid').setTitle('Pool');
          Ext.getCmp('poolingContainer').setLoading(false);
          new Noty({ text: 'Pool has been saved!' }).show();

          // Reload stores
          Ext.getStore('IndexGenerator').reload();
        } else {
          Ext.getCmp('poolingContainer').setLoading(false);
          new Noty({ text: obj.message, type: 'error' }).show();
        }
      },
      failure: function (response) {
        var errorMsg;
        try {
          var obj = Ext.JSON.decode(response.responseText);
          errorMsg = obj.message;
        } catch (error) {
          errorMsg = response.statusText;
        }
        new Noty({ text: errorMsg, type: 'error' }).show();

        if (errorMsg === 'Some of the indices are not unique.') {
          me.highlightNonUnique();
        }

        Ext.getCmp('poolingContainer').setLoading(false);
        console.error(response);
      }
    });
  },

  highlightNonUnique: function () {
    var grid = Ext.getCmp('pool-grid');
    var store = grid.getStore();
    var duplicates = {};

    var indexPairs = store.data.items.map(function (item) {
      return item.get('index_i7').index + item.get('index_i5').index;
    });

    for (var i = 0; i < indexPairs.length; i++) {
      if (duplicates.hasOwnProperty(indexPairs[i])) {
        duplicates[indexPairs[i]].push(i);
      } else if (indexPairs.lastIndexOf(indexPairs[i]) !== i) {
        duplicates[indexPairs[i]] = [i];
      }
    }

    var duplicateIndices = [].concat.apply([], Object.values(duplicates));

    grid.getSelectionModel().deselectAll();
    for (var j = 0; j < duplicateIndices.length; j++) {
      grid.getSelectionModel().select(duplicateIndices[j], true);
    }
  },

  // reset: function (record) {
  //   Ext.Ajax.request({
  //     url: 'index_generator/reset/',
  //     method: 'POST',
  //     timeout: 60000,
  //     scope: this,
  //     params: {
  //       status: 1,
  //       dilution_factor: 1,
  //       record_type: record.get('recordType'),
  //       record_id: record.get('recordType') === 'L' ? record.get('libraryId') : record.get('sampleId')
  //     },
  //     success: function (response) {
  //       var obj = Ext.JSON.decode(response.responseText);

  //       if (obj.success) {
  //         Ext.getCmp('pool-grid').setTitle('Pool');
  //         Ext.getStore('IndexGenerator').reload();
  //         new Noty({ text: 'The changes have been saved!' }).show();
  //       } else {
  //         new Noty({ text: obj.error, type: 'error' }).show();
  //       }
  //     },
  //     failure: function (response) {
  //       new Noty({ text: response.statusText, type: 'error' }).show();
  //       console.error(response);
  //     }
  //   });
  // },

  _isIndexTypeSet: function (store, record, showNotification) {
    var notif = showNotification === undefined;

    // Check if Index Type is set (only for samples)
    if (record.get('record_type') === 'Sample' && record.get('index_type') === 0) {
      if (notif) {
        new Noty({
          text: 'Index Type must be set.',
          type: 'warning'
        }).show();
      }
      return false;
    }

    return true;
  },

  // _isUnique: function (store, record, showNotification) {
  //   var notif = showNotification === undefined;
  //   if (store.getCount()) {
  //     var recordI7 = store.findRecord('indexI7', record.get('indexI7'));
  //     var recordI5 = store.findRecord('indexI5', record.get('indexI5'));

  //     if (recordI7 || recordI5) {
  //       if (notif) {
  //         new Noty({
  //           text: 'Selected index (I7/I5) is already in the pool.',
  //           type: 'warning'
  //         }).show();
  //       }
  //       return false;
  //     }
  //   }
  //   return true;
  // },

  _isCompatible: function (store, record, showNotification) {
    var notif = showNotification === undefined;

    if (store.getCount()) {
      var firstItem = store.getAt(0);
      var indexTypesStore = Ext.getStore('IndexTypes');
      var firstItemIndexType = indexTypesStore.findRecord(
        'id', firstItem.get('index_type'), 0, false, true, true);
      var recordIndexType = indexTypesStore.findRecord(
        'id', record.get('index_type'), 0, false, true, true);

      // Same Read Length
      if (firstItem.get('read_length') !== record.get('read_length')) {
        if (notif) {
          new Noty({
            text: 'Read lengths must be the same.',
            type: 'warning'
          }).show();
        }
        return false;
      }

      // No pooling of dual and single indices
      if (
        firstItemIndexType && recordIndexType &&
        firstItemIndexType.get('is_dual') !== recordIndexType.get('is_dual')
      ) {
        if (notif) {
          new Noty({
            text: 'Pooling of dual and single indices is not allowed.',
            type: 'warning'
          }).show();
        }
        return false;
      }

      // No pooling of indices with the length of 6 and 8 nucleotides (no mixed length)
      if (
        firstItemIndexType && recordIndexType &&
        firstItemIndexType.get('index_length') !== recordIndexType.get('index_length')
      ) {
        if (notif) {
          new Noty({
            text: 'Pooling of indices with 6 and 8 nucleotides (mixed) is not allowed.',
            type: 'warning'
          }).show();
        }
        return false;
      }
    }

    return true;
  },

  _isPoolSizeOk: function (store, record, multipleSelect) {
    var notif = !multipleSelect;
    var poolSizeId = Ext.getCmp('poolSizeCb').getValue();
    var poolSizeItem = Ext.getStore('PoolSizes').findRecord('id', poolSizeId, 0, false, true, true);
    var poolSize = store.sum('sequencing_depth') + record.get('sequencing_depth');

    if (poolSize > poolSizeItem.get('multiplier') * poolSizeItem.get('size')) {
      if (notif) {
        new Noty({
          text: 'You have exceeded the Pool Size. Please increase it.',
          type: 'warning'
        }).show();
      }
    }

    return true;
  },

  _resetGeneratedIndices: function () {
    var store = Ext.getCmp('pool-grid').getStore();

    store.each(function (record) {
      if (record.get('record_type') === 'Sample') {
        record.set({
          index_i7: '',
          index_i7_id: '',
          index_i5: '',
          index_i5_id: ''
        });

        for (var i = 0; i < 12; i++) {
          record.set('index_i7_' + (i + 1), '');
          record.set('index_i5_' + (i + 1), '');
        }
      }
    });
  },

  _isPoolValid: function (store) {
    var result = true;
    store.each(function (record) {
      if (record.get('index_i7_1') === '') {  // at least, indices I7 must be set
        result = false;
      }
    });
    return result;
  }
});
