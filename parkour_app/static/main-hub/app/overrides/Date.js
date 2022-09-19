// Add the diffPrecise() method to Ext.date
// adapted code from https://github.com/codebox/moment-precise-range
// (Precise range is a plugin for the moment.js library to display human-readable date/time ranges)
// diffPrecise uses two JS Object instances as arguments
// returns an object with precised period details, eg. the period between 2015-10-15 and 2016-11-16
// is represented as '1 year 1 month 1 day' instead of 1 year 13 months 398 days as will return the normal Ext.Date.diff()
// takes the time differences in account, also
Ext.define('MainHub.overrides.Date', {
  requires: 'Ext.Date'
}, function () {
  Ext.Date.diffPrecise = function (dMin, dMax, unitCaptions) {
    var STRINGS = {
      nodiff: '',
      year: 'year',
      years: 'years',
      month: 'month',
      months: 'months',
      day: 'day',
      days: 'days',
      hour: 'hour',
      hours: 'hours',
      minute: 'minute',
      minutes: 'minutes',
      second: 'second',
      seconds: 'seconds',
      delimiter: ' '
    };

    if (unitCaptions) {
      Ext.apply(STRINGS, unitCaptions);
    }

    if (Ext.Date.isEqual(dMin, dMax)) {
      // return STRINGS.nodiff;
    }

    if (dMin > dMax) {
      var tmp = dMin;
      dMin = dMax;
      dMax = tmp;
    }

    var yDiff = dMax.getFullYear() - dMin.getFullYear();
    var mDiff = dMax.getMonth() - dMin.getMonth();
    var dDiff = dMax.getDate() - dMin.getDate();
    var hourDiff = dMax.getHours() - dMin.getHours();
    var minDiff = dMax.getMinutes() - dMin.getMinutes();
    var secDiff = dMax.getSeconds() - dMin.getSeconds();

    if (secDiff < 0) {
      secDiff = 60 + secDiff;
      minDiff--;
    }

    if (minDiff < 0) {
      minDiff = 60 + minDiff;
      hourDiff--;
    }

    if (hourDiff < 0) {
      hourDiff = 24 + hourDiff;
      dDiff--;
    }

    if (dDiff < 0) {
      var daysInLastFullMonth = Ext.Date.getDaysInMonth(Ext.Date.subtract(dMax, Ext.Date.MONTH, 1));
      if (daysInLastFullMonth < dMin.getDate()) { // 31/01 -> 2/03
        dDiff = daysInLastFullMonth + dDiff + (dMin.getDate() - daysInLastFullMonth);
      } else {
        dDiff = daysInLastFullMonth + dDiff;
      }
      mDiff--;
    }

    if (mDiff < 0) {
      mDiff = 12 + mDiff;
      yDiff--;
    }

    function pluralize (num, word) {
      return num + ' ' + STRINGS[word + (num === 1 ? '' : 's')];
    }

    var result = [];

    if (yDiff) {
      result.push(pluralize(yDiff, 'year'));
    }
    if (mDiff) {
      result.push(pluralize(mDiff, 'month'));
    }
    if (dDiff) {
      result.push(pluralize(dDiff, 'day'));
    }
    if (hourDiff) {
      result.push(pluralize(hourDiff, 'hour'));
    }
    if (minDiff) {
      result.push(pluralize(minDiff, 'minute'));
    }
    if (secDiff) {
      result.push(pluralize(secDiff, 'second'));
    }

    var retObj = {};

    retObj.diffAsText = result.join(STRINGS.delimiter);
    Ext.apply(retObj, { years: yDiff, months: mDiff, days: dDiff, hours: hourDiff, minutes: minDiff, seconds: secDiff });
    return retObj;
  };
});
