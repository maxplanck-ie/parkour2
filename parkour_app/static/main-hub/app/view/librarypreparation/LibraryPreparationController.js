Ext.define('MainHub.view.librarypreparation.LibraryPreparationController', {
  extend: 'MainHub.components.BaseGridController',
  alias: 'controller.library-preparation',

  mixins: [
    'MainHub.grid.SearchInputMixin'
  ],

  config: {
    control: {
      '#': {
        activate: 'activateView'
      },
      '#library-preparation-grid': {
        resize: 'resize',
        itemcontextmenu: 'showMenu',
        groupcontextmenu: 'showGroupMenu',
        boxready: 'addToolbarButtons',
        edit: 'editRecord'
      },
      '#search-field': {
        change: 'changeFilter'
      },
      '#download-benchtop-protocol-button': {
        click: 'downloadBenchtopProtocol'
      },
      '#cancel-button': {
        click: 'cancel'
      },
      '#save-button': {
        click: 'save'
      }
    }
  },

  addToolbarButtons: function (grid) {
    grid.down('toolbar[dock="bottom"]').insert(0, {
      type: 'button',
      itemId: 'download-benchtop-protocol-button',
      text: 'Download Benchtop Protocol',
      iconCls: 'fa fa-file-excel-o fa-lg'
    });
  },

  editRecord: function (editor, context) {
    var store = editor.grid.getStore();
    var record = context.record;
    var changes = record.getChanges();
    var values = context.newValues;

    // Set nM
    if (
      Object.keys(changes).indexOf('nM') === -1 &&
      values.concentration_library > 0 &&
      values.mean_fragment_size > 0
    ) {
      var nM = this._calculateNM(
        values.concentration_library, values.mean_fragment_size);
      record.set('nM', nM);
    }

    // Send the changes to the server
    this.syncStore(store.getId());
  },

  applyToAll: function (gridView, record, dataIndex) {
    var self = this;
    var store = gridView.grid.getStore();
    var allowedColumns = [
      'starting_amount',
      'starting_volume',
      'spike_in_description',
      'spike_in_volume',
      'pcr_cycles',
      'concentration_library',
      'mean_fragment_size',
      'nM',
      'concentration_sample',
      'comments_facility',
      'comments',
      'qpcr_result'
    ];
    var nMFormulaDataIndices = [
      'concentration_library',
      'mean_fragment_size'
    ];

    if (dataIndex && allowedColumns.indexOf(dataIndex) !== -1) {
      store.each(function (item) {
        if (
          item.get(store.groupField) === record.get(store.groupField) &&
          item !== record
        ) {
          item.set(dataIndex, record.get(dataIndex));

          // Calculate nM
          if (nMFormulaDataIndices.indexOf(dataIndex) !== -1) {
            var concentrationLibrary = item.get('concentration_library');
            var meanFragmentSize = item.get('mean_fragment_size');
            if (concentrationLibrary && meanFragmentSize) {
              var nM = self._calculateNM(concentrationLibrary, meanFragmentSize);
              item.set('nM', nM);
            }
          }
        }
      });

      // Send the changes to the server
      self.syncStore(store.getId());
    } else {
      self._showEditableColumnsMessage(gridView, allowedColumns);
    }
  },

  downloadBenchtopProtocol: function (btn) {
    var store = btn.up('grid').getStore();
    var ids = [];

      // Get all checked (selected) records
    store.each(function (record) {
      if (record.get('selected')) {
        ids.push(record.get('pk'));
      }
    });

    if (ids.length === 0) {
      new Noty({
        text: 'You did not select any samples.',
        type: 'warning'
      }).show();
      return;
    }

    var form = Ext.create('Ext.form.Panel', { standardSubmit: true });
    form.submit({
      url: 'api/library_preparation/download_benchtop_protocol/',
      params: { 'ids': Ext.JSON.encode(ids) }
    });
  },

  _calculateNM: function (concentration, meanFragmentSize) {
    return ((parseFloat(concentration) / (parseFloat(meanFragmentSize) * 650)) * 1000000).toFixed(2);
  }
});
