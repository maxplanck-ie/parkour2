/**
 * Private utility class for Ext.Splitter.
 * @private
 */
Ext.define("Ext.resizer.SplitterTracker", {
  extend: "Ext.dd.DragTracker",
  requires: ["Ext.util.Region"],
  enabled: true,

  overlayCls: Ext.baseCSSPrefix + "resizable-overlay",

  createDragOverlay: function () {
    var overlay,
      El = Ext.dom.Element;

    overlay = this.overlay = Ext.getBody().createChild({
      role: "presentation",
      cls: this.overlayCls,
      html: "&#160;"
    });

    overlay.unselectable();
    overlay.setSize(El.getDocumentWidth(), El.getDocumentHeight());
    overlay.show();
  },

  getPrevCmp: function () {
    var splitter = this.getSplitter();
    return splitter.previousSibling(":not([hidden])");
  },

  getNextCmp: function () {
    var splitter = this.getSplitter();
    return splitter.nextSibling(":not([hidden])");
  },

  // ensure the tracker is enabled, store boxes of previous and next
  // components and calculate the constrain region
  onBeforeStart: function (e) {
    var me = this,
      prevCmp = me.getPrevCmp(),
      nextCmp = me.getNextCmp(),
      collapseEl = me.getSplitter().collapseEl,
      target = e.getTarget(),
      box;

    if (!prevCmp || !nextCmp) {
      return false;
    }

    if (collapseEl && target === collapseEl.dom) {
      return false;
    }

    // SplitterTracker is disabled if any of its adjacents are collapsed.
    if (nextCmp.collapsed || prevCmp.collapsed) {
      return false;
    }

    // store boxes of previous and next
    me.prevBox = prevCmp.getEl().getBox();
    me.nextBox = nextCmp.getEl().getBox();
    me.constrainTo = box = me.calculateConstrainRegion();

    if (!box) {
      return false;
    }

    return box;
  },

  onMouseDown: function (e, target) {
    // Logic to resize components. If this splitter has an iframe on either side,
    // dragging over it will make us not detect startDrag, so we need to cover all iframes and
    // this has to be done before triggerStart or onStart. We cannot do this in
    // general (meaning adding this to Ext.dd.DragTracker) because other draggable things cannot
    // assume that mouseDown is safe for this purpose. In particular ComponentDragger on a maximizable window will
    // get tricked by the maximize button onMouseDown and mask everything but will
    // never get the onMouseUp to unmask the iframes.
    this.callParent([e, target]);

    if (this.mouseIsDown && this.getSplitter().el.dom === target) {
      Ext.dom.Element.maskIframes();
    }
  },

  onMouseUp: function (e) {
    this.callParent([e]);
    Ext.dom.Element.unmaskIframes();
  },

  // We move the splitter el. Add the proxy class.
  onStart: function (e) {
    var splitter = this.getSplitter();
    this.createDragOverlay();
    splitter.addCls(splitter.baseCls + "-active");
  },

  onResizeKeyDown: function (e) {
    var me = this,
      splitter = me.getSplitter(),
      key = e.getKey(),
      incrIdx = splitter.orientation === "vertical" ? 0 : 1,
      incr = key === e.UP || key === e.LEFT ? -1 : 1,
      easing;

    if (!me.active && me.onBeforeStart(e)) {
      Ext.fly(e.target).on("keyup", me.onResizeKeyUp, me);
      me.triggerStart(e);
      me.onMouseDown(e);
      me.startXY = splitter.getXY();
      me.lastKeyDownXY = Ext.Array.slice(me.startXY);

      // Movement increment eases to 4 over two seconds.
      easing = me.easing = new Ext.fx.easing.Linear();
      easing.setStartTime(Ext.Date.now());
      easing.setStartValue(1);
      easing.setEndValue(4);
      easing.setDuration(2000);
    }
    if (me.active) {
      me.lastKeyDownXY[incrIdx] = Math.round(
        me.lastKeyDownXY[incrIdx] + incr * me.easing.getValue()
      );
      me.lastXY = me.lastKeyDownXY;
      splitter.setXY(me.getXY("dragTarget"));
    }
  },

  onResizeKeyUp: function (e) {
    this.onMouseUp(e);
  },

  // calculate the constrain Region in which the splitter el may be moved.
  calculateConstrainRegion: function () {
    var me = this,
      splitter = me.getSplitter(),
      splitWidth = splitter.getWidth(),
      defaultMin = splitter.defaultSplitMin,
      orient = splitter.orientation,
      prevBox = me.prevBox,
      prevCmp = me.getPrevCmp(),
      nextBox = me.nextBox,
      nextCmp = me.getNextCmp(),
      // prev and nextConstrainRegions are the maximumBoxes minus the
      // minimumBoxes. The result is always the intersection
      // of these two boxes.
      prevConstrainRegion,
      nextConstrainRegion,
      constrainOptions;

    // vertical splitters, so resizing left to right
    if (orient === "vertical") {
      constrainOptions = {
        prevCmp: prevCmp,
        nextCmp: nextCmp,
        prevBox: prevBox,
        nextBox: nextBox,
        defaultMin: defaultMin,
        splitWidth: splitWidth
      };
      // Region constructor accepts (top, right, bottom, left)
      // anchored/calculated from the left
      prevConstrainRegion = new Ext.util.Region(
        prevBox.y,
        me.getVertPrevConstrainRight(constrainOptions),
        prevBox.bottom,
        me.getVertPrevConstrainLeft(constrainOptions)
      );
      // anchored/calculated from the right
      nextConstrainRegion = new Ext.util.Region(
        nextBox.y,
        me.getVertNextConstrainRight(constrainOptions),
        nextBox.bottom,
        me.getVertNextConstrainLeft(constrainOptions)
      );
    } else {
      // anchored/calculated from the top
      prevConstrainRegion = new Ext.util.Region(
        prevBox.y + (prevCmp.minHeight || defaultMin),
        prevBox.right,
        // Bottom boundary is y + maxHeight if there IS a maxHeight.
        // Otherwise it is calculated based upon the minWidth of the next Component
        (prevCmp.maxHeight
          ? prevBox.y + prevCmp.maxHeight
          : nextBox.bottom - (nextCmp.minHeight || defaultMin)) + splitWidth,
        prevBox.x
      );
      // anchored/calculated from the bottom
      nextConstrainRegion = new Ext.util.Region(
        // Top boundary is bottom - maxHeight if there IS a maxHeight.
        // Otherwise it is calculated based upon the minHeight of the previous Component
        (nextCmp.maxHeight
          ? nextBox.bottom - nextCmp.maxHeight
          : prevBox.y + (prevCmp.minHeight || defaultMin)) - splitWidth,
        nextBox.right,
        nextBox.bottom - (nextCmp.minHeight || defaultMin),
        nextBox.x
      );
    }

    // intersection of the two regions to provide region draggable
    return prevConstrainRegion.intersect(nextConstrainRegion);
  },

  // Performs the actual resizing of the previous and next components
  performResize: function (e, offset) {
    var me = this,
      splitter = me.getSplitter(),
      orient = splitter.orientation,
      prevCmp = me.getPrevCmp(),
      nextCmp = me.getNextCmp(),
      owner = splitter.ownerCt,
      flexedSiblings = owner.query(">[flex]"),
      len = flexedSiblings.length,
      vertical = orient === "vertical",
      i = 0,
      dimension = vertical ? "width" : "height",
      totalFlex = 0,
      item,
      size;

    // Convert flexes to pixel values proportional to the total pixel width of all flexes.
    for (; i < len; i++) {
      item = flexedSiblings[i];
      size = vertical ? item.getWidth() : item.getHeight();
      totalFlex += size;
      item.flex = size;
    }

    offset = vertical ? offset[0] : offset[1];

    if (prevCmp) {
      size = me.prevBox[dimension] + offset;
      if (prevCmp.flex) {
        prevCmp.flex = size;
      } else {
        prevCmp[dimension] = size;
      }
    }
    if (nextCmp) {
      size = me.nextBox[dimension] - offset;
      if (nextCmp.flex) {
        nextCmp.flex = size;
      } else {
        nextCmp[dimension] = size;
      }
    }

    owner.updateLayout();
  },

  // Cleans up the overlay (if we have one) and calls the base. This cannot be done in
  // onEnd, because onEnd is only called if a drag is detected but the overlay is created
  // regardless (by onBeforeStart).
  endDrag: function () {
    var me = this;

    if (me.overlay) {
      me.overlay.destroy();
      delete me.overlay;
    }

    me.callParent(arguments); // this calls onEnd
  },

  // perform the resize and remove the proxy class from the splitter el
  onEnd: function (e) {
    var me = this,
      splitter = me.getSplitter();

    splitter.removeCls(splitter.baseCls + "-active");
    me.performResize(e, me.getResizeOffset());
  },

  // Track the proxy and set the proper XY coordinates
  // while constraining the drag
  onDrag: function (e) {
    var me = this,
      offset = me.getOffset("dragTarget"),
      splitter = me.getSplitter(),
      splitEl = splitter.getEl(),
      orient = splitter.orientation;

    if (orient === "vertical") {
      splitEl.setX(me.startRegion.left + offset[0]);
    } else {
      splitEl.setY(me.startRegion.top + offset[1]);
    }
  },

  getSplitter: function () {
    return this.splitter;
  },

  getVertPrevConstrainRight: function (o) {
    // Right boundary is x + maxWidth if there IS a maxWidth.
    // Otherwise it is calculated based upon the minWidth of the next Component
    return (
      (o.prevCmp.maxWidth
        ? o.prevBox.x + o.prevCmp.maxWidth
        : o.nextBox.right - (o.nextCmp.minWidth || o.defaultMin)) + o.splitWidth
    );
  },

  getVertPrevConstrainLeft: function (o) {
    return o.prevBox.x + (o.prevCmp.minWidth || o.defaultMin);
  },

  getVertNextConstrainRight: function (o) {
    return o.nextBox.right - (o.nextCmp.minWidth || o.defaultMin);
  },

  getVertNextConstrainLeft: function (o) {
    // Left boundary is right - maxWidth if there IS a maxWidth.
    // Otherwise it is calculated based upon the minWidth of the previous Component
    return (
      (o.nextCmp.maxWidth
        ? o.nextBox.right - o.nextCmp.maxWidth
        : o.prevBox.x + (o.prevBox.minWidth || o.defaultMin)) - o.splitWidth
    );
  },

  getResizeOffset: function () {
    return this.getOffset("dragTarget");
  }
});
