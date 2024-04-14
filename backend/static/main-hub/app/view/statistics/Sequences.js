Ext.define("MainHub.view.statistics.Sequences", {
  extend: "Ext.container.Container",
  xtype: "sequences-statistics",

  requires: [
    "MainHub.components.BaseGrid",
    "MainHub.components.SearchField",
    "MainHub.view.statistics.SequencesController",
    "Ext.ux.DateRangePicker",
  ],

  controller: "sequences-statistics",

  anchor: "100% -1",
  layout: "fit",

  items: [
    {
      xtype: "basegrid",
      itemId: "sequences-grid",
      store: "SequencesStatistics",
      height: Ext.Element.getViewportHeight() - 64,
      sortableColumns: true,

      header: {
        title: "Sequences",
        items: [
          {
            xtype: "checkbox",
            boxLabel:
              '<span data-qtip="Check, to show only the requests for which you are responsible">As Handler</span>',
            itemId: "as-handler-sequences-checkbox",
            margin: "0 15 0 0",
            cls: "grid-header-checkbox",
            hidden: !USER.is_staff,
            checked: false,
          },
          {
            xtype: "checkbox",
            boxLabel:
              '<span data-qtip="Check, to show only the requests for which you are responsible for data analysis">As Bioinformatician</span>',
            itemId: "as-bioinformatician-sequences-checkbox",
            margin: "0 15 0 0",
            cls: "grid-header-checkbox",
            hidden: !USER.is_bioinformatician,
            checked: false,
          },
          {
            xtype: "checkbox",
            boxLabel:
              '<span data-qtip="Uncheck, to show data per individual lane">Merge lanes</span>',
            itemId: "merge-lanes-sequences-checkbox",
            margin: "0 15 0 0",
            cls: "grid-header-checkbox",
            checked: true,
          },
          {
            xtype: "parkoursearchfield",
            store: "SequencesStatistics",
            emptyText: "Search",
            width: 320,
          },
        ],
      },

      columns: {
        defaults: {
          flex: 1,
        },
        items: [
          {
            xtype: "checkcolumn",
            itemId: "check-column",
            dataIndex: "selected",
            resizable: false,
            menuDisabled: true,
            hideable: false,
            tdCls: "no-dirty",
            width: 35,
          },
          {
            text: "Request",
            dataIndex: "request",
            renderer: "gridCellTooltipRenderer",
            filter: { type: "string" },
            minWidth: 135,
          },
          {
            text: "Barcode",
            dataIndex: "barcode",
            filter: { type: "string" },
            minWidth: 135,
          },
          {
            text: "Name",
            dataIndex: "name",
            renderer: "gridCellTooltipRenderer",
            filter: { type: "string" },
            minWidth: 135,
          },
          {
            text: "Lane",
            dataIndex: "lane",
            filter: { type: "string" },
            minWidth: 135,
          },
          {
            text: "Pool",
            dataIndex: "pool",
            filter: { type: "string" },
            minWidth: 135,
          },
          {
            text: "Library Protocol",
            dataIndex: "library_protocol",
            renderer: "gridCellTooltipRenderer",
            filter: { type: "string" },
            minWidth: 135,
          },
          {
            text: "Library Type",
            dataIndex: "library_type",
            renderer: "gridCellTooltipRenderer",
            filter: { type: "string" },
            minWidth: 135,
          },
          {
            text: "M Reads PF, requested",
            dataIndex: "reads_pf_requested",
            filter: { type: "number" },
            minWidth: 135,
            renderer: function (value, meta, record) {
              var readsSequenced = record.get("reads_pf_sequenced");

              if (readsSequenced && value) {
                var diff = readsSequenced - value * 1000000;
                if (diff < 0) {
                  meta.tdCls += " invalid-record";
                }
              }

              return value;
            },
          },
          {
            text: "M Reads PF, sequenced",
            dataIndex: "reads_pf_sequenced",
            renderer: function (value, meta, record) {
              var readsRequested = record.get("reads_pf_requested");
              value = value ? value : 0;

              if (readsRequested && value) {
                var diff = value - readsRequested * 1000000;
                if (diff < 0) {
                  meta.tdCls += " invalid-record";
                }
              }

              if (value) {
                value = (value / 1000000).toFixed(2);
              }

              return value;
            },
            filter: { type: "number" },
            minWidth: 135,
          },
          {
            text: "% reads",
            renderer: function (value, meta, record) {
              var readsSequenced = record.get("reads_pf_sequenced");
              var totalReads = record.get("total_reads");
              if (readsSequenced) {
                // If total_reads cannot be retrieved, calculate it
                if (!totalReads) {
                  var store = this.store;
                  var grouping = store.getGroups().items.filter(function (g) {
                    return g.getGroupKey() == record.get("pk");
                  });
                  if (grouping.length === 1) {
                    var totalReads = grouping[0].sum("reads_pf_sequenced");
                  }
                }
                value = ((readsSequenced / totalReads) * 100).toFixed(2);
              }
              return value;
            },
            minWidth: 135,
          },
          {
            text: "confident off-species reads",
            tooltip: "confident off-species reads",
            dataIndex: "confident_reads",
            renderer: floatRenderer,
            filter: { type: "number" },
            minWidth: 135,
            hidden: true,
          },
          {
            text: "% Optical Duplicates",
            tooltip: "% Optical Duplicates",
            dataIndex: "optical_duplicates",
            renderer: floatRenderer,
            filter: { type: "number" },
            minWidth: 135,
            hidden: true,
          },
          {
            text: "% dupped reads",
            tooltip: "% dupped reads",
            dataIndex: "dupped_reads",
            renderer: floatRenderer,
            filter: { type: "number" },
            minWidth: 135,
            hidden: true,
          },
          {
            text: "% mapped reads",
            tooltip: "% mapped reads",
            dataIndex: "mapped_reads",
            renderer: floatRenderer,
            filter: { type: "number" },
            minWidth: 135,
            hidden: true,
          },
          {
            text: "Insert Size",
            dataIndex: "insert_size",
            filter: { type: "number" },
            minWidth: 135,
            hidden: true,
          },
        ],
      },

      plugins: [
        {
          ptype: "bufferedrenderer",
          trailingBufferZone: 100,
          leadingBufferZone: 100,
        },
        {
          ptype: "gridfilters",
        },
        {
          ptype: "clipboard",
        },
      ],

      features: [
        {
          ftype: "grouping",
          id: "sequences-grid-grouping",
          startCollapsed: true,
          enableGroupingMenu: false,
          groupHeaderTpl: [
            "<strong>{children:this.getFlowcellId} " +
              "({children:this.getDate}, {children:this.getSequencingKit}, {children:this.getTotalYield} M reads PF)</strong>",
            {
              getFlowcellId: function (children) {
                return children[0].get("flowcell_id");
              },
              getDate: function (children) {
                return Ext.util.Format.date(children[0].get("create_time"));
              },
              getSequencingKit: function (children) {
                return children[0].get("sequencing_kit");
              },
              getTotalYield: function (children) {
                var total_reads = children.reduce(function (sum, e) {
                  return sum + e.get("reads_pf_sequenced");
                }, 0);
                // Set total_reads on all children of group, so that it does
                // not have to be recalculated again later when the % reads
                // of each child is computed
                children.forEach(function (c) {
                  c.set("total_reads", total_reads);
                });
                return (total_reads / 1000000).toFixed(1);
              },
            },
          ],
        },
      ],

      dockedItems: [
        {
          xtype: "toolbar",
          dock: "top",
          items: [
            {
              xtype: "daterangepicker",
              ui: "header",
              drpDefaults: {
                showButtonTip: false,
                dateFormat: "d.m.Y",
                mainBtnTextColor: "#999",
                mainBtnIconCls: "x-fa fa-calendar",
                presetPeriodsBtnIconCls: "x-fa fa-calendar-check-o",
                confirmBtnIconCls: "x-fa fa-check",
              },
            },
          ],
        },
        {
          xtype: "toolbar",
          dock: "bottom",
          items: [
            {
              text: "Download Report",
              itemId: "download-report",
              iconCls: "fa fa-download fa-lg",
            },
          ],
        },
      ],
    },
  ],
});

function floatRenderer(value) {
  if (value) {
    value = value.toFixed(2);
  }
  return value;
}
