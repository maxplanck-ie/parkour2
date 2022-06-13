Web API
=======

Parkour provides a web API that can be used to facilitate both downstream processing and returning of alignment and other metrics back for record keeping and potential future analysis.

Examples below are given in python using python 3, though any programming language could be used in practice provided it can construct JSON strings.

General considerations
----------------------

The user account used to interact with the web API must have "staff" permissions. Further, since the password is used for authentication, you are strongly encouraged to ensure that this password cannot be read by other users.

Submitting per-lane statistics to Parkour
-----------------------------------------

Illumina sequencing runs produce a variety of metrics that are useful to track. These include:

 - The percentage of clusters that pass filtering
 - The number of reads passing filtering
 - The percentage of reads with undetermined indices
 - The percentages of bases (for read 1 and read 2) with quality scores of at least 30

The `api/run_statistics/upload` URL can be used to submit metrics of this sort per-lane per-flowcell. To do so, one must first create a JSON string of the following form::

    {
      "matrix": [
        {
          "name": "Lane 1",
          "cluster_pf": "90.41",
          "reads_pf": "107641925",
          "undetermined_indices": "9.26%",
          "read_2": "85.23",
          "read_1": "94.08"
        },
        {
          "name": "Lane 2",
          "cluster_pf": "90.39",
          "reads_pf": "105981493",
          "undetermined_indices": "9.31%",
          "read_2": "85.04",
          "read_1": "94.11"
        }
      ],
      "flowcell_id": "HVKWLBGX7"
    }

The `flowcell_id` should match what is in Parkour. The rest of the content is that described above, where `cluster_pf` is the percentage of clusters passing filtering, `reads_pf` is the number of reads passing filtering, `undeterminded_indices` is the percentage of reads with undetermined indices, and `read_1` and `read_2` are the percentages of bases in reads 1 and 2 with quality scores of at least 30. The following python code demonstrates how to submit this to Parkour::

    import json
    import requests

    URL = "https://parkour-demo.ie-freiburg.mpg.de/api/run_statistics/upload"
    user = "some email address"
    password = "A password that you should keep secret!"

    d = dict()
    d['flowcell_id'] = "HVKWLBGX7"
    m = [{
          "name": "Lane 1",
          "cluster_pf": "90.41",
          "reads_pf": "107641925",
          "undetermined_indices": "9.26%",
          "read_2": "85.23",
          "read_1": "94.08"
        },
        {
          "name": "Lane 2",
          "cluster_pf": "90.39",
          "reads_pf": "105981493",
          "undetermined_indices": "9.31%",
          "read_2": "85.04",
          "read_1": "94.11"
        }]
    d['matrix'] = json.dumps(m)
    res = requests.post(URL, auth=(user, password), data=d)

Within Parkour, users with "staff" accounts can view these metrics by clicking on "Statistics" and then "Runs".


Query Parkour for information on a flowcell
-------------------------------------------

In order to process samples, downstream processes need to know the following information:

 1. What organism the sample comes from.
 2. The type of experiment (e.g., RNA-seq or ChIP-seq) a sample comes from.
 3. The library preparation protocol.

This can be queried on a per-flowcell basis using the `api/analysis_list/analysis_list/` web API. This take a single `GET` query with a flowcell ID that must already exist in Parkour::

    import requests

    URL = "https://parkour-demo.ie-freiburg.mpg.de/api/analysis_list/analysis_list/"
    user = "some email address"
    password = "A password that you should keep secret!"

    d = {"flowcell_id": "HVKWLBGX7"}
    res = requests.get(URL, auth=(user, password), params=d)
    if res.status_code == 200:
        # do something with res.json()

An example of the output is as follows::

    {
     "528_Ryan_Boenisch": {
                           "18L008007": ['Input', 'ChIP-Seq', 'NEBNext Ultra II DNA Library Prep Kit for Illumina', 'mouse'],
                           "18L008008": ['H3K4me3', 'ChIP-Seq', 'NEBNext Ultra II DNA Library Prep Kit for Illumina', 'mouse']
                          },
     "529_Anatskiy_Manke": {
                           "18L008009": ['Brain', 'single-cell RNA-seq', '10xGenomics for single cell RNA-Seq', 'mouse'],
                           "18L008010": ['Liver', 'single-cell RNA-seq', '10xGenomics for single cell RNA-Seq', 'mouse']
                          }
    }

The result is a dictionary of dictionaries. Each element of the outer-most dictionary is a single project in Parkour (`528_Ryan_Boenisch` in this case). The inner-most dictionary has keys of the library ID (e.g., `18L008007`) and values an orderd list of: sample name, library type, library protocol, and organism.


Reporting downstream metrics back to Parkour
--------------------------------------------

Standard metrics such as alignment rate can be returned to Parkour so that the sequencing facility can track how changes to library preparation protocols affect downstream results. The downstream and per-sample metrics that we report back include:

 1. Reads passing filter (`reads_pf_sequenced`)
 2. Confidently off-species alignment rate (`confident_reads`)
 3. Optical duplication rate (`optical_duplicates`)
 4. Percentage mapped (`mapped_reads`)
 5. Percentage marked as duplicates (`dupped_reads`)
 6. Median insert size (`insert_size`)

Each of these metrics is optional! To submit these metrics back to Parkour, one can use the `api/sequences_statistics/upload/` URL with a POST method. As above, a JSON string is created that stores each of these metrics and associates them to a library ID::

    import requests
    import json

    URL = "https://parkour-demo.ie-freiburg.mpg.de/api/sequences_statistics/upload/"
    user = "some email address"
    password = "A password that you should keep secret!"

    m = [{"barcode": "18L008007",
          "reads_pf_sequenced": 123456,
          "confident_reads": 0.001,
          "optical_duplicates": 0.01,
          "mapped_reads": 95.20,
          "dupped_reads": 5.23,
          "insert_size": 150},
         {"barcode": "18L008008",
          "reads_pf_sequenced": 250743,
          "confident_reads": 0.003,
          "optical_duplicates": 0.02,
          "mapped_reads": 94.71,
          "dupped_reads": 4.92,
          "insert_size": 152}]

    d = {"flowcell_id": "HVKWLBGX7"}
    d['sequences'] = json.dumps(m)
    res = requests.post(URL, auth=(user, password), data=d)

Users with "staff" accounts can then view this metrics from within Parkour by clicking on "Statistics" and then "Sequences".
