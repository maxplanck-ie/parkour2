===============
Index Generator
===============

Sample Selection
################

Index Generator is one of the central components in Parkour LIMS. The tool groups samples by compatible index types and run conditions and assigns generated indices to them. The Index Generator chooses indices from predefined lists to ensure proper image registration on sequencing devices.

All samples or libraries with status quality approved will appear in the Index Generator for either index assignment or index validations. On the left side of the window, grouped by request, you can select libraries and samples for grouping and index validation or assignment.

Before starting working with the samples, you need to make sure that a Pool Size is specified (by selecting an option in the corresponding drop down menu). Ideally, you shouldn’t exceed the chosen Pool Size, but you will still be able to save the samples as a pool.

You can group only those libraries and samples if they have:

* the same read length

* compatible index type

  - The same index length (6 or 8 nucleotides)

  - Either Index I7 (single index ) or Index I7 + Index I5 (dual index)

Index Type is required to be set for all samples to proceed.

The Index Generator can handle different index types and formats such as single- and dual-indexing in individual tubes or standard 96-well plates.

Index Generation
################

After you selected libraries and samples, you should see them on the right side of the window.

.. _index-generator:

.. figure:: img/index_generator.png
    :figwidth: 100 %
    :align: center

    Index Generator.

Now you can click the Generate Indices button. If all the requirements to the Pool Size and Index Types are met, you should be able to see the newly generated indices. Otherwise, a corresponding message(s) will appear.

Index Generator shows the color diversity of the generated indices as a ratio between the green (G/T) and red (A/C) nucleotides per column. Balanced signal in both the channels (red and green) is a prerequisite for proper image registration and base calling on Illuminas’ sequencing instruments.

When indices have been generated, you can save the selected libraries and samples as a pool. For best organization and simple tracking a running number is assigned to each pool. The generated pool number is completely independent of the pooled/grouped requests. After index generation and pool saving, samples will disappear from the right side of the index generator window and appear in the next stage of the workflow.

To maximize sample throughput, facilitate shallow sequencing and sequencing of small sample batches (do not fill complete lanes) the index generator provides the following grouping options.

A pool can consist of libraries only. To this the index generator displays index diversity of the already assigned indices and allows index saving only if none of the indices is duplicated. For dual indexed libraries the index generator allows duplicates in i5 or i7 index sequence, but rejects duplicated i5 or i7 index pairs.

A pool can consist of samples only. To this the index generator generates and assigns indices as described above.

A pool can contain samples and libraries. To do this, the index generator displays index sequence of libraries and assigns on top of those libraries indices to samples from predefined lists.

There are two principal approaches to the index generation.

Randomized
~~~~~~~~~~

If the number of selected samples is less than a certain threshold, Index Generator will randomly pick an index for the first sample and then generate indices for the remaining samples, maximizing the color diversity score by reaching to the 50%/50% ratio as close as possible. Indices will be assigned to samples in an ascending order, based on the numbering of each index. This ensures simple and immaculate handling of index tubes during sample preparation in a laboratory.

Subsequent Indices
~~~~~~~~~~~~~~~~~~

If the samples are set to have a 96-well plate index type, Index Generator will take subsequent index pairs (predefined Index I7 + Index I5 pairs), starting from a certain position and direction. By default the start position is A1 and the direction is right.

Assume we have a 9-well plate:

.. _nine-well-plate:

.. table:: 9-well plate.
    :widths: auto

    +---+-------------+-------------+-------------+
    |   |      1      |      2      |      3      |
    +===+=============+=============+=============+
    | A | I7_1 - I5_1 | I7_2 - I5_1 | I7_3 - I5_1 |
    +---+-------------+-------------+-------------+
    | B | I7_1 - I5_2 | I7_2 - I5_2 | I7_3 - I5_2 |
    +---+-------------+-------------+-------------+
    | C | I7_1 - I5_3 | I7_2 - I5_3 | I7_3 - I5_3 |
    +---+-------------+-------------+-------------+

Depending on the selected direction, Index Generator will consider index pairs in the following order:

* **Right**: A1, A2, A3, B1, … , C3
* **Down**: A1, B1, C1, A2, … , C3
* **Diagonal**: A1, B2, C3, A2, … , C2

The start position controls the first position to be considered. For example, given the start position B3 and the direction down, the index pairs will be taken in the following order: B3, C3, A1, B1, … , A3.

