Ext.define("validator.Unique", {
  extend: "Ext.data.validator.Validator",
  alias: "data.validator.unique",
  validate: function (value, record) {
    var dataIndex = this.dataIndex;
    var store = record.store;
    var values = [];

    store.each(function (item) {
      var currentValue = item.get(dataIndex);
      if (item !== record && currentValue !== "") {
        values.push(currentValue);
      }
    });

    return values.indexOf(value) === -1 || "Must be unique";
  }
});

Ext.define("validator.GreaterThanZero", {
  extend: "Ext.data.validator.Validator",
  alias: "data.validator.greaterthanzero",
  validate: function (value) {
    return value > 0 || "Must be greater than 0";
  }
});

Ext.define("validator.GreaterThanTen", {
  extend: "Ext.data.validator.Validator",
  alias: "data.validator.greaterthanten",
  validate: function (value) {
    return value >= 10 || "Must be greater or equal to 10";
  }
});

Ext.define("MainHub.model.libraries.BatchAdd.Common", {
  extend: "Ext.data.Model",

  fields: [
    {
      type: "string",
      name: "name"
    },
    {
      name: "measuring_unit",
      type: "string"
    },
    {
      name: "measured_value",
      type: "float",
      allowNull: true,
      defaultValue: null
    },
    {
      type: "int",
      name: "library_protocol",
      allowNull: true,
      defaultValue: null
    },
    {
      type: "int",
      name: "library_type",
      allowNull: true,
      defaultValue: null
    },
    {
      type: "float",
      name: "sequencing_depth",
      defaultValue: null
    },
    {
      name: "volume",
      type: "float",
      defaultValue: null
    },
    {
      type: "int",
      name: "read_length",
      allowNull: true,
      defaultValue: null
    },
    {
      type: "int",
      name: "organism",
      allowNull: true,
      defaultValue: null
    },
    {
      type: "string",
      name: "comments"
    },
    {
      type: "bool",
      name: "invalid",
      defaultValue: false
    },
    {
      type: "auto",
      name: "errors",
      defaultValue: {}
    }
  ],

  validators: {
    name: [
      {
        type: "presence"
      },
      {
        type: "unique",
        dataIndex: "name"
      }
    ],
    measuring_unit: "presence",
    library_protocol: "presence",
    library_type: "presence",
    volume: "greaterthanten",
    read_length: "presence",
    sequencing_depth: "greaterthanten",
    organism: "presence"
  }
});
