#Generates .tsv and report and determines readiness for QC
#


#Questions:
# Need TSV file. Need to label
# What to do if sample did not succeed?


import csv
import os
import sys
import glob
import datetime
import argparse
import subprocess
from string import Template

desc_str =""""
    Program to generate WGBS report.
"""

parser = argparse.ArgumentParser(description=desc_str)
parser.add_argument("-w", type=str, help='woid')
parser.add_argument("-fw",type=str,help="file of woid\'s (no header)")
args = parser.parse_args()

id_list = []

if args.w:
    id_list.append(args.w)
elif args.fw:
    with open(args.fw) as woid_file:
        for line in woid_file:
            id_list.append(line.rstrip())
else:
    sys.exit('-w for single workorder\n-fw for file of work orders w/o header')

mm_dd_yy = datetime.datetime.now().strftime('%m%d%y')
template_dict = ['WOID', 'SAMPLE_NUMBER', 'status', 'TSV_LOCATION', 'MODEL_GROUP_ID']

for work_order in id_list:

    outfile = '{}.report.{}.txt'.format(work_order,mm_dd_yy)
    tsv_file = '{}.results.{}.tsv'.format(work_order,mm_dd_yy)

    genome_com_out = subprocess.check_output(['genome', 'model', 'list', 'model_groups.project.id={}'.format(work_order),
                             '--show', 'name,subject.name,last_succeeded_build.id,last_succeeded_build.data_directory,'
                                       'processing_profile,last_succeeded_build.date_completed,status','--style=tsv']).decode("utf-8")

    genome_out_split = genome_com_out.split('\n')
    header = genome_out_split[0].split('\t')
    genome_data = genome_com_out.split('\n')[1:]

    with open(tsv_file,'w') as of:
        row = csv.writer(of,delimiter = '\t')
        row.writerow(header)
        row.writerows([x.split('\t') for x in genome_data])

    sample_count = 0
    succeeded_count = 0
    with open(tsv_file, 'r') as rf:
        data_dict = csv.DictReader(rf, delimiter = '\t')

        for line in data_dict:
            if line['status'] == 'Succeeded':
                succeeded_count +=1
            sample_count +=1

    if sample_count == 0:
        print('No report generated for {} as no samples were found'.format(work_order))
        sys.exit()
    else:
        model_group_id = subprocess.check_output(['genome', 'model-group', 'list', '-f', 'project.id={}'.format(work_order),
                                                  '--show', 'id', '--style=tsv', '--noheaders']).decode('utf-8')

        #Check for template
        if not os.path.isfile('/gscmnt/gc2783/qc/GMSworkorders/reports/WGBS_report_template.txt'):
           sys.exit('\nTemplate file not found.')

        #Open and create template file using Template;
        with open('/gscmnt/gc2783/qc/GMSworkorders/reports/WGBS_report_template.txt', 'r', encoding='utf-8') as fh:
            template = fh.read()
            template_file = Template(template)


            with open(outfile, 'w', encoding='utf-8') as fh:

                fh.write(template_file.substitute(WOID = work_order,
                                                  SAMPLE_NUMBER = sample_count,
                                                  status= succeeded_count,
                                                  MODEL_GROUP_ID = model_group_id,
                                                  TSV_LOCATION = tsv_file))
                print('Report for {} generated'.format(work_order))
