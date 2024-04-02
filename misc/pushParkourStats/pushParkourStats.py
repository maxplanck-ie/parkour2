import os
import argparse
import xml.etree.ElementTree as ET
import json
from urllib.parse import urljoin
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import subprocess
import csv
from io import StringIO

import requests
import interop
import numpy as np
import pandas as pd


# Configs
CONFIG = {'PARKOUR_BASE_URL': os.environ.get('PARKOUR_BASE_URL', 'https://parkour.url.com/'),
          'PARKOUR_USER': os.environ.get('PARKOUR_USER', 'parkourUserEmail'),
          'PARKOUR_USER_PASSWORD': os.environ.get('PARKOUR_USER_PASSWORD', 'parkourUserPassword'),
          'PARKOUR_EMAIL_HOST': os.environ.get('PARKOUR_EMAIL_HOST', 'host.address.com'),
          'PARKOUR_EMAIL_PORT': os.environ.get('PARKOUR_EMAIL_PORT', 25),
          'PARKOUR_FROM_ADDRESS': os.environ.get('PARKOUR_FROM_ADDRESS', 'sender@example.com'),
          'PARKOUR_TO_ADDRESSES': os.environ.get('PARKOUR_TO_ADDRESSES', 'alias1@example.com,alias2@example.com').split(','),
          }


def parse_cmd_args():
    "Parse command-line arguments"

    description = '''Push run and demultiplexing stats to Parkour.
                     The following environment variables must be set:
                       PARKOUR_BASE_URL, e.g. https://parkour.url.com/;
                       PARKOUR_USER, e.g. parkourUserEmail;
                       PARKOUR_USER_PASSWORD, e.g. parkourUserPassword;
                       PARKOUR_EMAIL_HOST, e.g. host.address.com;
                       PARKOUR_EMAIL_PORT, e.g. 25;
                       PARKOUR_FROM_ADDRESS, e.g. sender@example.com;
                       PARKOUR_TO_ADDRESSES, e.g. alias1@example.com,alias2@example.com (comma-separated
                       list of email addresses).
                  '''

    cmd_arg_parser = argparse.ArgumentParser(prog='pushParkourStats',
                                             description=description)
    cmd_arg_parser.add_argument(
        '--flowcellDir', required=True, help='Path to the folder containg InterOp')
    cmd_arg_parser.add_argument('--bclFlowcellOutDir', required=True,
                                help='Path to the folder containg Reports/Quality_Metrics.csv')
    return cmd_arg_parser.parse_args()


def sendMail(message, config):
    'Adapted from dissectBCL.fakeNews.mailHome'

    mailer = MIMEMultipart()
    mailer['Subject'] = '[Parkour] Pushing run statistics to Parkour failed'
    mailer['From'] = config.get('PARKOUR_FROM_ADDRESS')
    mailer['To'] = ','.join(config.get('PARKOUR_TO_ADDRESSES', []))
    email = MIMEText(message, 'plain')
    mailer.attach(email)
    s = smtplib.SMTP(config.get('PARKOUR_EMAIL_HOST'),
                     port=config.get('PARKOUR_EMAIL_PORT', 25))
    s.sendmail(
        config.get('PARKOUR_FROM_ADDRESS'),
        config.get('PARKOUR_TO_ADDRESSES', []),
        mailer.as_string()
    )
    s.quit()


def getFlowcellId(run_info_path):
    '''
    Takes the path to runInfo.xml and parses it.
    Returns:
        - the flowcellID (str)

    Adapted from dissectBCL.classes.flowCellClass.parseRunInfo
    '''
    tree = ET.parse(run_info_path)
    root = tree.getroot()
    for i in root.iter():
        if i.tag == 'Flowcell':
            flowcellID = i.text
    return flowcellID


def pushParkour(flowcellID: str, bclFlowcellOutDir: str,
                flowcellBase: str, config: dict[str: str]) -> None:
    '''
    Push run stats and demultiplex sequences to Parkour
    Adapted from from dissectBCL.fakeNews.pushParkour

    cluster_count
    cluster_count_pf
    cluster_pf
    density
    density_pf
    name (Lane name)
    perc_reads_pf
    read_x (Same as read_1_perc_q30)
    read_x_error_rate
    read_x_first_cycle_int
    read_x_perc_aligned
    read_x_perc_q30
    undetermined_indices
    '''

    def pushRunStats(flowcellID: str, bclFlowcellOutDir: str,
                     flowcellBase: str, config: dict[str: str]) -> None:

        def get_matrix_py_interop(bclFlowcellOutDir: str,
                                  flowcellBase: str) -> str:
            """Get run QC metrics using Python's interop library"""

            # Parse interop
            try:
                iop_df = pd.DataFrame(
                    interop.summary(
                        interop.read(
                            flowcellBase
                        ),
                        'Lane'
                    )
                )
            except:
                raise Exception('Cannot find/open Interop folder '
                                'for flowcell {flowcellID}')

            laneDict = {}
            # Get Quality_Metrics.csv
            try:
                qdf = pd.read_csv(os.path.join(bclFlowcellOutDir,
                                               'Reports',
                                               'Quality_Metrics.csv'))
            except:
                raise Exception('Cannot find/open Quality_Metrics.csv '
                                'for flowcell {flowcellID}')

            # Loop through lanes
            for lane in list(qdf['Lane'].unique()):
                subdf = qdf[qdf['Lane'] == lane]
                laneStr = f'Lane {lane}'
                laneDict[laneStr] = {}

                # Reads PF
                readsPF = iop_df[(iop_df['ReadNumber'] == 1) &
                                 (iop_df['Lane'] == lane)] \
                                ['Reads Pf'].values[0]
                laneDict[laneStr]['reads_pf'] = int(round(float(readsPF), 0))

                # % reads PF
                percReadsPF = iop_df[(iop_df['ReadNumber'] == 1) &
                                     (iop_df['Lane'] == lane)] \
                                    ['% Pf'].values[0]
                laneDict[laneStr]['perc_reads_pf'] = round(
                    float(percReadsPF), 2)

                # Cluster count
                clusterCount = iop_df[(iop_df['ReadNumber'] == 1) &
                                      (iop_df['Lane'] == lane)] \
                                     ['Cluster Count'].values[0]
                laneDict[laneStr]['cluster_count'] = int(clusterCount)

                # Cluster count PF
                clusterCountPF = iop_df[(iop_df['ReadNumber'] == 1) &
                                        (iop_df['Lane'] == lane)] \
                                       ['Cluster Count Pf'].values[0]
                laneDict[laneStr]['cluster_count_pf'] = int(round(float(clusterCountPF), 0))

                # Density
                density = iop_df[(iop_df['ReadNumber'] == 1) &
                                 (iop_df['Lane'] == lane)] \
                               ['Density'].values[0]
                laneDict[laneStr]['density'] = int(density)

                # Density PF
                densityPF = iop_df[(iop_df['ReadNumber'] == 1) &
                                   (iop_df['Lane'] == lane)] \
                                  ['Density Pf'].values[0]
                laneDict[laneStr]['density_pf'] = int(densityPF)

                # Undetermined indices
                laneDict[laneStr]["undetermined_indices"] = \
                    round(
                        subdf[subdf["SampleID"] == "Undetermined"]["YieldQ30"].sum() \
                            / subdf['YieldQ30'].sum() * 100,
                        2)

                # % reads Q30, same as read_1_perc_q30 below
                # Do not consider libraries for which the yield is 0 reads
                # because these also have 0 % Q30
                Q30Dic = subdf.query('Yield > 0').groupby("ReadNumber")['% Q30'].mean().to_dict()
                for read in Q30Dic:
                    if 'I' not in str(read):
                        readStr = f'read_{read}'
                        laneDict[laneStr][readStr] = round(Q30Dic[read]*100, 2)
                laneDict[laneStr]["cluster_pf"] = round(
                    subdf["YieldQ30"].sum()/subdf["Yield"].sum() * 100,
                    2
                )

                # Other fields, per read
                fieldNames = {'Error Rate': 'error_rate',
                              'First Cycle Intensity': 'first_cycle_int',
                              '% Aligned': 'perc_aligned',
                              '% >= Q30': 'perc_q30'}
                for fieldName, fieldId in fieldNames.items():
                    tempDic = iop_df.query(
                        "Lane == @lane")[['ReadNumber', fieldName]]
                    for _, (read, val) in tempDic.iterrows():
                        if not pd.isna(val) and 'I' not in str(read):
                            readStr = f'read_{int(read)}_{fieldId}'
                            laneDict[laneStr][readStr] = round(val, 2)

                laneDict[laneStr]["name"] = laneStr

            return json.dumps(list(laneDict.values()))

        def get_matrix_illumina_interop(flowcellBase: str) -> str:
            """Get run QC metrics using interop_summary, backup for when
            the main get_matrix_py_interop function fails"""

            try:
                # Get interop_summary as CSV
                interop_summary_cmd = f'interop_summary {flowcellBase}'
                interop_summary = subprocess.run(interop_summary_cmd.split(),
                                                 capture_output=True, text=True)
                interop_summary = StringIO(interop_summary.stdout)
                interop_summary = csv.reader(interop_summary, delimiter=',')
                interop_summary = [r for r in interop_summary]
            except:
                raise Exception('Cannot find/open Interop folder for flowcell {flowcellID}')

            # Get run QC data per Read
            headers = [c.strip() for c in [r for r in interop_summary
                                           if len(r) == 20][0]]
            data = [[c.split(' ')[0] for c in r] for r in interop_summary
                    if len(r) == 20 and r[1].strip() == '-']
            data = pd.DataFrame(data, columns=headers)

            try:
                # Only keep relevant columns
                relevant_headers = ['Lane', 'Density', 'Cluster PF',
                                    'Reads PF', '%>=Q30', 'Aligned',
                                    'Error', 'Intensity C1']
                data = data.loc[:, relevant_headers]
            except:
                raise Exception('Cannot find relevant headers in Interop summary for flowcell {flowcellID}')

            # Set read numbers
            num_reads = len(data.query('Lane == "1"'))
            num_lanes = data['Lane'].nunique()
            data['Read'] = [i for i in range(1, num_reads + 1) for _ in range(num_lanes)]

            # Convert text to numbers
            data = data.astype(float)

            # Set new header names
            new_headers = ['name', 'density', 'cluster_pf',
                           'reads_pf', "read_{rn}_perc_q30",
                           "read_{rn}_perc_aligned", "read_{rn}_error_rate",
                           "read_{rn}_first_cycle_int", 'read_number']
            data.columns = new_headers

            # Replace NaN with None
            data = data.replace(np.nan, None)

            # Beautify data
            data['density'] = data['density'].astype(int)
            data['density'] = data['density']*10**3
            data['reads_pf'] = (data['reads_pf']*10**6).astype(int)
            data['name'] = data['name'].astype(int)
            data['read_number'] = data['read_number'].astype(int)
            data['read_{rn}_first_cycle_int'] = data['read_{rn}_first_cycle_int'].astype(int)

            # Creat matrix to be uploaded
            matrix = []

            # Loop through lanes
            for lane in data['name'].unique():

                # Get data for all reads in a lane
                lane_data = data.query('name == @lane').iloc[:, 1:]
                lane_dict = {'name': f'Lane {lane}'}

                # Loop through reads
                for row in lane_data.itertuples(index=False, name=None):

                    # Get read number
                    read_number = row[-1]

                    # Add data available for a read to matrix
                    for h, val in zip(new_headers[1:], row[:-1]):
                        lane_dict[h.format(rn=read_number)] = val

                        # read_x should be the same as read_x_perc_q30
                        if h.endswith('perc_q30'):
                            lane_dict[f'read_{read_number}'] = val

                matrix.append(lane_dict)

            return json.dumps(matrix)

        d = {'flowcell_id': flowcellID}

        # Get the matrix, try first with get_matrix_pyinterop
        # if that does not work, use get_matrix_illinterop
        errors = []
        try:
            d['matrix'] = get_matrix_py_interop(bclFlowcellOutDir, flowcellBase)
        except Exception as exp:
            errors.append(exp)
            try:
                d['matrix'] = get_matrix_illumina_interop(flowcellBase)
            except Exception as exp:
                errors.append(exp)
                raise Exception('\n'.join([str(e).format(flowcellID=flowcellID) for e in errors]))

        pushParkourRunStat = requests.post(
            urljoin(config.get("PARKOUR_BASE_URL"),
                    'api/run_statistics/upload/'),
            auth=(
                config.get("PARKOUR_USER"),
                config.get("PARKOUR_USER_PASSWORD")
            ),
            data=d,
            verify=True,
            timeout=10
        )

        if pushParkourRunStat.status_code != 200:
            raise Exception(
                f"Cannot push run statistics for flowcell {flowcellID}. Error: {pushParkourRunStat.text}")

    def pushSequenceStats(flowcellID: str, bclFlowcellOutDir: str,
                          config: dict[str: str]) -> None:

        # Get demultiplexStatsdf.csv
        try:
            demultiplexStatsdf = pd.read_csv(os.path.join(bclFlowcellOutDir,
                                                          'Reports', 'Demultiplex_Stats.csv'))
        except:
            raise Exception('Cannot find/open Demultiplex_Stats.csv '
                            f'for flowcell {flowcellID}')

        # Get Sample name <-> Barcode
        samplesBarcodesdf = pullParkourSamplesBarcodes(flowcellID, config)
        # Match demultiplexStatsdf and samplesBarcodesdf on SampleID
        demultiplexStatsdf = pd.merge(demultiplexStatsdf, samplesBarcodesdf,
                                      on='SampleID', how='left')
        # Polish new df a bit
        demultiplexStatsdf = demultiplexStatsdf[['Barcode', 'SampleID',
                                                 '# Reads', "Lane"]]
        demultiplexStatsdf.columns = ["barcode","name",
                                      "reads_pf_sequenced", "lane"]
        demultiplexStatsdf["barcode"] = demultiplexStatsdf["barcode"].fillna("")
        demultiplexStatsdf["reads_pf_sequenced"] = demultiplexStatsdf["reads_pf_sequenced"]. \
                                                   astype(pd.Int64Dtype())
        demultiplexStatsdf["lane"] = demultiplexStatsdf["lane"].astype(pd.Int64Dtype())

        d = {"flowcell_id": flowcellID}
        d['sequences'] = demultiplexStatsdf[["barcode", "name",
                                            "reads_pf_sequenced", "lane"]].to_json(orient="records")
        pushParkourSequencesStats = requests.post(
            urljoin(config.get("PARKOUR_BASE_URL"),
                    'api/sequences_statistics/upload/'),
            auth=(config.get("PARKOUR_USER"),
                 config.get("PARKOUR_USER_PASSWORD")),
            data=d,
            verify=True,
            timeout=10
        )

        if pushParkourSequencesStats.status_code != 200:
            raise Exception(f'Cannot push run statistics for flowcell {flowcellID}. '
                            f'Error: {pushParkourSequencesStats.text}')

    if '-' in flowcellID:
        flowcellID = flowcellID.split('-')[1]

    errors = []

    try:
        pushRunStats(flowcellID, bclFlowcellOutDir, flowcellBase, config)
    except Exception as exp:
        errors.append(exp)

    try:
        pushSequenceStats(flowcellID, bclFlowcellOutDir, config)
    except Exception as exp:
        errors.append(exp)

    if errors:
        raise Exception('\n'.join([str(e) for e in errors]))


def pullParkourSamplesBarcodes(flowcellID: str,
                               config: dict[str: str]) -> pd.DataFrame:
    """
    Get the contents of a flowcell and extract 
    library name and barcode
    """

    FID = flowcellID
    if '-' in FID:
        FID = FID.split('-')[1]

    d = {'flowcell_id': FID}
    pullParkourFlowcellContents = requests.get(
        urljoin(config.get("PARKOUR_BASE_URL"),
                'api/analysis_list/analysis_list/'),
        auth=(
            config.get('PARKOUR_USER'),
            config.get('PARKOUR_USER_PASSWORD')
        ),
        params=d,
        verify=True,
        timeout=10
    )
    if pullParkourFlowcellContents.status_code == 200:

        samplesBarcodesLis = []
        json_data = pullParkourFlowcellContents.json()
        for _, libs in json_data.items():
            for barcode, lib_props in libs.items():
                samplesBarcodesLis.append((lib_props[0], barcode))
        return pd.DataFrame.from_records(samplesBarcodesLis, columns=['SampleID', 'Barcode'])
    else:
        raise Exception(f'Cannot pull flowcell details for flowcell {flowcellID}. '
                        f'Error: {pullParkourFlowcellContents.text}')


def main(bclFlowcellOutDir: str, flowcellBase: str, config: dict[str: str]) -> str:

    flowcellID = getFlowcellId(os.path.join(flowcellBase, 'RunInfo.xml'))

    pushParkour(flowcellID, bclFlowcellOutDir, flowcellBase, config)

    return flowcellID


if __name__ == '__main__':

    try:
        cmd_args = parse_cmd_args()

        flowcellID = main(cmd_args.bclFlowcellOutDir,
                          cmd_args.flowcellDir,
                          CONFIG)
    except Exception as exp:
        sendMail(str(exp), CONFIG)
        raise exp

    print(f'Successfully pushed stats to Parkour for flowcell {flowcellID}')
