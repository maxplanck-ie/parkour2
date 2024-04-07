Ext.define("MainHub.view.statistics.RunStatistics", {
  extend: "Ext.container.Container",
  xtype: "run-statistics",

  requires: [
    "MainHub.components.BaseGrid",
    "MainHub.components.MonthPicker",
    "MainHub.components.SearchField",
    "MainHub.view.statistics.RunStatisticsController",
    "Ext.ux.DateRangePicker"
  ],

  controller: "run-statistics",

  anchor: "100% -1",
  layout: "fit",

  items: [
    {
      xtype: "basegrid",
      id: "run-statistics-grid",
      itemId: "run-statistics-grid",
      store: "RunStatistics",
      height: Ext.Element.getViewportHeight() - 64,

      header: {
        title: "Run Statistics",
        items: [
          {
            xtype: "checkbox",
            boxLabel:
              '<span data-qtip="Check, to show only the requests for which you are responsible">As Handler</span>',
            itemId: "as-handler-statistics-checkbox",
            margin: "0 15 0 0",
            cls: "grid-header-checkbox",
            hidden: !USER.is_staff,
            checked: false,
          },
          {
            xtype: "checkbox",
            boxLabel:
              '<span data-qtip="Check, to show only the requests for which you are responsible for data analysis">As bioinformatician</span>',
            itemId: "as-bioinformatician-statistics-checkbox",
            margin: "0 15 0 0",
            cls: "grid-header-checkbox",
            hidden: !USER.is_bioinformatician,
            checked: false,
          },
          {
            xtype: "parkoursearchfield",
            store: "RunStatistics",
            emptyText: "Search",
            paramName: "pool",
            width: 320
          }
        ]
      },

      columns: {
        defaults: {
          minWidth: 135,
          flex: 1
        },
        items: [
          {
            text: "Lane",
            dataIndex: "name",
            minWidth: 35
          },
          {
            text: "Pool",
            dataIndex: "pool",
            minWidth: 35,
            filter: { type: "string" }
          },
          {
            text: "Request",
            dataIndex: "request",
            minWidth: 120,
            filter: { type: "string" }
          },
          {
            text: "Prep. Method",
            dataIndex: "library_preparation",
            tooltip: "Preparation Method",
            minWidth: 110,
            filter: { type: "list" }
          },
          {
            text: "Library Type",
            dataIndex: "library_type",
            minWidth: 100,
            filter: { type: "list" }
          },
          {
            text: "Loaded pM",
            dataIndex: "loading_concentration",
            tooltip: "Loading concentration of pool in pM",
            minWidth: 90,
            filter: { type: "number" }
          },
          {
            text: "% Cluster PF",
            dataIndex: "cluster_pf",
            minWidth: 100,
            filter: { type: "number" }
          },
          {
            text: "M Reads PF",
            dataIndex: "reads_pf",
            minWidth: 95,
            filter: { type: "number" },
            renderer: function (value) {
              if (value) {
                value = (value / 1000000).toFixed(1);
              }
              return value;
            }
          },
          {
            text: "% Undet. Indices",
            dataIndex: "undetermined_indices",
            tooltip: "% undetermined indices",
            minWidth: 125,
            filter: { type: "number" }
          },
          {
            text: "% PhiX (E / O)",
            dataIndex: "phix",
            tooltip: "% PhiX, expected / observed",
            minWidth: 105,
            renderer: function (value, meta, record, rowIndex) {
              
              expected = value ? value : 'NA';
              observed = record.get('read_1_perc_aligned') ? 
                         record.get('read_1_perc_aligned') : 'NA';

              return Ext.String.format(
                '{0} / {1}',
                expected,
                observed
              );
            }
          },
          {
            text: "R1, % ≥Q30",
            dataIndex: "read_1",
            minWidth: 90,
            filter: { type: "number" }
          },
          {
            text: "R1, 1st cycle int.",
            dataIndex: "read_1_first_cycle_int",
            tooltip: "1st cycle intensity for Read 1",
            minWidth: 120,
            filter: { type: "number" }
          },
          {
            text: "R1, error rate",
            dataIndex: "read_1_error_rate",
            minWidth: 105,
            filter: { type: "number" }
          },
          {
            text: "R2 (I), % ≥Q30",
            dataIndex: "read_2",
            minWidth: 105,
            filter: { type: "number" }
          }
        ]
      },

      plugins: [
        {
          ptype: "bufferedrenderer",
          trailingBufferZone: 100,
          leadingBufferZone: 100
        },
        {
          ptype: "gridfilters"
        }
      ],

      features: [
        {
          ftype: "grouping",
          id: "run-statistics-grid-grouping",
          startCollapsed: true,
          enableGroupingMenu: false,
          groupHeaderTpl: [
            "<strong>{children:this.getFlowcellId} " +
              "({children:this.getDate}, {children:this.getSequencer}, " +
              "{children:this.getReadLength})</strong>",
            {
              getFlowcellId: function (children) {
                return children[0].get("flowcell_id");
              },
              getDate: function (children) {
                return Ext.util.Format.date(children[0].get("create_time"));
              },
              getSequencer: function (children) {
                return children[0].get("sequencer");
              },
              getReadLength: function (children) {
                return children[0].get("read_length");
              }
            }
          ]
        }
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
                confirmBtnIconCls: "x-fa fa-check"
              }
            }
          ]
        }
      ]
    }
  ]
});
