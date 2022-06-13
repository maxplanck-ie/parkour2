=========
Invoicing
=========

An automated invoicing system is part of the Parkour LIMS. Each request, that reaches status “Sequencing”, will appear in the “Invoicing” tab. Processed requests are presented per month. For data editing and sharing information needs to be download into a spreadsheet. An upload functions is installed for documentation of final cost reports.

Price calculation is based on predefined costs for service, consumables and reagents. Princes are stored in Parkour and are freely editable.

Prices are calculated for sample preparation or performed quality control by multiplication of the number of samples, that reach the status “quality approved”, times costs for the respective protocol. If prepared libraries are submitted to Parkour, preparation costs are calculated by multiplication of the number of approved libraries times preset costs for quality control per sample.
Prices for sequencing of samples are calculated by multiplication of requested sequencing depth times preset prices for sequencing on a certain instrument with preset run conditions. Note that the user is billed exclusively for the number of requested reads.

Final costs for a request are the sum of the calculated costs for sample preparation (can be a quality control only) and the calculated costs for sequencing. Additionally, to account for labor and instrument usage, overhead costs can be added to the calculated costs for preparation and sequencing.
