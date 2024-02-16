import os
import argparse
import xml.etree.ElementTree as ET
import json
from urllib.parse import urljoin
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

import requests
import interop
import pandas as pd


# Configs
CONFIG = {'baseURL': 'https://parkour.url.com/',
          'user': 'parkourUserEmail',
          'password': 'parkourUserPassword',
          'emailHost': 'host.address.com',
          'emailPort': 25,
          'fromAddress': 'sender@example.com',
          'toAddresses': ['alias1@example.com', 'alias2@example.com'],
          }


def parse_cmd_args():
    "Parse command-line arguments"

    cmd_arg_parser = argparse.ArgumentParser(prog='pushParkourStats',
                                             description='Push run and demultiplexing stats to Parkour')
    cmd_arg_parser.add_argument(
        '--flowcellDir', required=True, help='Path to the folder containg InterOp')
    cmd_arg_parser.add_argument('--bclFlowcellOutDir', required=True,
                                help='Path to the folder containg Reports/Quality_Metrics.csv')
    return cmd_arg_parser.parse_args()


def sendMail(message, config):
    'Adapted from dissectBCL.fakeNews.mailHome'

    mailer = MIMEMultipart()
    mailer['Subject'] = '[Parkour] Pushing run statistics to Parkour failed'
    mailer['From'] = config.get('fromAddress')
    mailer['To'] = ','.join(config.get('toAddresses', []))
    email = MIMEText(message, 'plain')
    mailer.attach(email)
    s = smtplib.SMTP(config.get('emailHost'), port=config.get('emailPort', 25))
    s.sendmail(
        config.get('fromAddress'),
        config.get('toAddresses', []),
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


def pushParkour(flowcellID, bclFlowcellOutDir, flowcellBase, config):
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

    def pushRunStats(flowcellID, bclFlowcellOutDir, flowcellBase, config):

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
            raise Exception(
                f'Cannot find/open Interop folder for flowcell {flowcellID}')

        # Push Run Stats

        d = {}
        d['flowcell_id'] = flowcellID
        laneDict = {}

        # Get Quality_Metrics.csv

        try:
            qdf = pd.read_csv(os.path.join(bclFlowcellOutDir,
                                        'Reports', 'Quality_Metrics.csv'))
        except:
            raise Exception(
                f'Cannot find/open Quality_Metrics.csv for flowcell {flowcellID}')

        # Loop through lanes
        for lane in list(qdf['Lane'].unique()):
            subdf = qdf[qdf['Lane'] == lane]
            laneStr = f'Lane {lane}'
            laneDict[laneStr] = {}

            # Reads PF
            readsPF = iop_df[
                (iop_df['ReadNumber'] == 1) & (iop_df['Lane'] == lane)
            ]['Reads Pf'].values[0]
            laneDict[laneStr]['reads_pf'] = int(round(float(readsPF), 0))

            # % reads PF
            percReadsPF = iop_df[
                (iop_df['ReadNumber'] == 1) & (iop_df['Lane'] == lane)
            ]['% Pf'].values[0]
            laneDict[laneStr]['perc_reads_pf'] = round(float(percReadsPF), 2)

            # Cluster count
            clusterCount = iop_df[
                (iop_df['ReadNumber'] == 1) & (iop_df['Lane'] == lane)
            ]['Cluster Count'].values[0]
            laneDict[laneStr]['cluster_count'] = int(clusterCount)

            # Cluster count PF
            clusterCountPF = iop_df[
                (iop_df['ReadNumber'] == 1) & (iop_df['Lane'] == lane)
            ]['Cluster Count Pf'].values[0]
            laneDict[laneStr]['cluster_count_pf'] = int(
                round(float(clusterCountPF), 0))

            # Density
            density = iop_df[
                (iop_df['ReadNumber'] == 1) & (iop_df['Lane'] == lane)
            ]['Density'].values[0]
            laneDict[laneStr]['density'] = int(density)

            # Density PF
            densityPF = iop_df[
                (iop_df['ReadNumber'] == 1) & (iop_df['Lane'] == lane)
            ]['Density Pf'].values[0]
            laneDict[laneStr]['density_pf'] = int(densityPF)

            # Undetermined indices
            laneDict[laneStr]["undetermined_indices"] = \
                round(
                    subdf[
                        subdf["SampleID"] == "Undetermined"
                    ]["YieldQ30"].sum() / subdf['YieldQ30'].sum() * 100,
                    2
            )

            # % reads Q30, same as read_1_perc_q30 below
            Q30Dic = subdf.groupby("ReadNumber")['% Q30'].mean().to_dict()
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
                tempDic = iop_df.query("Lane == @lane")[['ReadNumber', fieldName]]
                for _, (read, val) in tempDic.iterrows():
                    if not pd.isna(val) and 'I' not in str(read):
                        readStr = f'read_{int(read)}_{fieldId}'
                        laneDict[laneStr][readStr] = round(val, 2)

            laneDict[laneStr]["name"] = laneStr

        d['matrix'] = json.dumps(list(laneDict.values()))

        pushParkourRunStat = requests.post(
            urljoin(config.get("baseURL"), 'api/run_statistics/upload/'),
            auth=(
                config.get("user"),
                config.get("password")
            ),
            data=d,
            verify=True,
            timeout=10
        )

        if pushParkourRunStat.status_code != 200:
            raise Exception(
                f"Cannot push run statistics for flowcell {flowcellID}. Error: {pushParkourRunStat.text}")

    def pushSequenceStats(flowcellID, bclFlowcellOutDir, config):

        # Get demultiplexStatsdf.csv
        try:
            demultiplexStatsdf = pd.read_csv(os.path.join(bclFlowcellOutDir,
                                                        'Reports', 'Demultiplex_Stats.csv'))
        except:
            raise Exception(
                f'Cannot find/open Demultiplex_Stats.csv for flowcell {flowcellID}')

        # Get Sample name <-> Barcode
        samplesBarcodesdf = pullParkourSamplesBarcodes(flowcellID, config)
        # Match demultiplexStatsdf and samplesBarcodesdf on SampleID
        demultiplexStatsdf = pd.merge(
            demultiplexStatsdf, samplesBarcodesdf, on='SampleID', how='left')
        # Polish new df a bit
        demultiplexStatsdf = demultiplexStatsdf[[
            'Barcode', 'SampleID', '# Reads', "Lane"]]
        demultiplexStatsdf.columns = ["barcode",
                                    "name", "reads_pf_sequenced", "lane"]
        demultiplexStatsdf["barcode"] = demultiplexStatsdf["barcode"].fillna("")
        demultiplexStatsdf["reads_pf_sequenced"] = demultiplexStatsdf["reads_pf_sequenced"].astype(
            pd.Int64Dtype())
        demultiplexStatsdf["lane"] = demultiplexStatsdf["lane"].astype(
            pd.Int64Dtype())

        d = {"flowcell_id": flowcellID}
        d['sequences'] = demultiplexStatsdf[["barcode", "name",
                                            "reads_pf_sequenced", "lane"]].to_json(orient="records")
        pushParkourSequencesStats = requests.post(
            urljoin(config.get("baseURL"), 'api/sequences_statistics/upload/'),
            auth=(
                config.get("user"),
                config.get("password")
            ),
            data=d,
            verify=True,
            timeout=10
        )

        if pushParkourSequencesStats.status_code != 200:
            raise Exception(
                f"Cannot push run statistics for flowcell {flowcellID}. Error: {pushParkourSequencesStats.text}")

    if '-' in flowcellID:
        flowcellID = flowcellID.split('-')[1]

    pushRunStats(flowcellID, bclFlowcellOutDir, flowcellBase, config)
    pushSequenceStats(flowcellID, bclFlowcellOutDir, config)


def pullParkourSamplesBarcodes(flowcellID, config):
    """
    Get the contents of a flowcell and extract 
    library name and barcode
    """

    FID = flowcellID
    if '-' in FID:
        FID = FID.split('-')[1]

    d = {'flowcell_id': FID}
    pullParkourFlowcellContents = requests.get(
        urljoin(config.get("baseURL"), 'api/analysis_list/analysis_list/'),
        auth=(
            config.get('user'),
            config.get('password')
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
        raise Exception(
            f"Cannot pull flowcell details for flowcell {flowcellID}. Error: {pullParkourFlowcellContents.text}")


def main(bclFlowcellOutDir, flowcellBase, config):

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
