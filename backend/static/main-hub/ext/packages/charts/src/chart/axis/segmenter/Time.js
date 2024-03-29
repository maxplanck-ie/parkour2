/**
 * @class Ext.chart.axis.segmenter.Time
 * @extends Ext.chart.axis.segmenter.Segmenter
 *
 * Time data type.
 */
Ext.define("Ext.chart.axis.segmenter.Time", {
  extend: "Ext.chart.axis.segmenter.Segmenter",
  alias: "segmenter.time",

  config: {
    /**
     * @cfg {Object} step
     * @cfg {String} step.unit The unit of the step (Ext.Date.DAY, Ext.Date.MONTH, etc).
     * @cfg {Number} step.step The number of units for the step (1, 2, etc).
     * If specified, will override the result of {@link #preferredStep}.
     * For example:
     *
     *     step: {
     *         unit: Ext.Date.HOUR,
     *         step: 1
     *     }
     */
    step: null
  },

  renderer: function (value, context) {
    var ExtDate = Ext.Date;
    switch (context.majorTicks.unit) {
      case "y":
        return ExtDate.format(value, "Y");
      case "mo":
        return ExtDate.format(value, "Y-m");
      case "d":
        return ExtDate.format(value, "Y-m-d");
    }
    return ExtDate.format(value, "Y-m-d\nH:i:s");
  },

  from: function (value) {
    return new Date(value);
  },

  diff: function (min, max, unit) {
    if (isFinite(min)) {
      min = new Date(min);
    }
    if (isFinite(max)) {
      max = new Date(max);
    }
    return Ext.Date.diff(min, max, unit);
  },

  updateStep: function () {
    var axis = this.getAxis();

    if (axis && !this.isConfiguring) {
      axis.performLayout();
    }
  },

  align: function (date, step, unit) {
    if (unit === "d" && step >= 7) {
      date = Ext.Date.align(date, "d", step);
      date.setDate(date.getDate() - date.getDay() + 1);
      return date;
    } else {
      return Ext.Date.align(date, unit, step);
    }
  },

  add: function (value, step, unit) {
    return Ext.Date.add(new Date(value), unit, step);
  },

  stepUnits: [
    [Ext.Date.YEAR, 1, 2, 5, 10, 20, 50, 100, 200, 500],
    [Ext.Date.MONTH, 1, 3, 6],
    [Ext.Date.DAY, 1, 7, 14],
    [Ext.Date.HOUR, 1, 6, 12],
    [Ext.Date.MINUTE, 1, 5, 15, 30],
    [Ext.Date.SECOND, 1, 5, 15, 30],
    [Ext.Date.MILLI, 1, 2, 5, 10, 20, 50, 100, 200, 500]
  ],

  preferredStep: function (min, estStepSize) {
    if (this.getStep()) {
      return this.getStep();
    }
    var from = new Date(+min),
      to = new Date(+min + Math.ceil(estStepSize)),
      units = this.stepUnits,
      result,
      unit,
      diff,
      i,
      j;

    for (i = 0; i < units.length; i++) {
      unit = units[i][0];
      diff = this.diff(from, to, unit);

      if (diff > 0) {
        for (j = 1; j < units[i].length; j++) {
          if (diff <= units[i][j]) {
            result = {
              unit: unit,
              step: units[i][j]
            };
            break;
          }
        }
        if (!result) {
          i--;
          result = {
            unit: units[i][0],
            step: 1
          };
        }
        break;
      }
    }
    if (!result) {
      result = { unit: Ext.Date.DAY, step: 1 }; // Default step is one Day.
    }
    return result;
  }
});
