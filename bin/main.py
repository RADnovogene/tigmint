#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @File    : main.py
# @Date    : 19-1-2
# @Author  : luyang(luyang@novogene.com)
import configparser
import os
import re
import subprocess
import sys

class CaseConfigParser(configparser.ConfigParser):
    def __init__(self, defaults=None):
        configparser.ConfigParser.__init__(self, defaults=None)

    def optionxform(self, optionstr):
        return optionstr

def mapping(config):
    work_dir = config['general']['work_dir']
    mapping_nums = int(config['general']['mapping_nums'])
    with open(work_dir + '/05.script/index_mapping.sh', 'a') as f:
        f.write('''#!/usr/bin/env bash
export PATH={bwa}:$PATH
export PATH={samtools}:$PATH

cd {work_dir}/03.tigmint
bwa index {work_dir}/03.tigmint/draft.fa
samtools faidx {work_dir}/03.tigmint/draft.fa
'''.format(**config['general']))
    for i in range(mapping_nums):
        with open(work_dir + '/05.script/mapping.' + str(i) + '.sh', 'a') as f:
            f.write('''#!/usr/bin/env bash
export PATH={bwa}:$PATH
export PATH={samtools}:$PATH

cd {work_dir}/01.mapping
bwa mem -t 8 -p -C {work_dir}/03.tigmint/draft.fa {work_dir}/02.basic/basic_{0}/outs/barcoded.fastq.gz | samtools sort -@ 8 -t BX -o {work_dir}/03.mapping/draft.reads_{0}.sortbx.bam
'''.format(i,**config['general']))
    with open(work_dir + '/05.script/merge.sh', 'a') as f:
        f.write('''#!/usr/bin/env bash
export PATH={samtools}:$PATH

cd {work_dir}/01.mapping
samtools merge -t BX {work_dir}/01.mapping/draft.reads.sortbx.bam {work_dir}/01.mapping/draft.reads_*.sortbx.bam 
'''.format(**config['general']))

def longranger(config):
    work_dir = config['general']['work_dir']
    mapping_nums = int(config['general']['mapping_nums'])
    for i in range(mapping_nums):
        with open(work_dir + '/05.script/basic.' + str(i) + '.sh', 'a') as f:
            f.write('''#!/usr/bin/env bash
export PATH={longranger}:$PATH

cd {work_dir}/02.basic
longranger basic --fastqs={work_dir}/00.reads/{0} --id=basic_{0} --sample=XG
'''.format(i,**config['general']))

def tigmint_cut(config):
    work_dir = config['general']['work_dir']
    with open(work_dir + '/05.script/tigmint_cut.sh', 'a') as f:
        f.write('''#!/usr/bin/env bash
export PATH={tigmint}:$PATH

cd {work_dir}/03.tigmint
'''.format(**config['general']))
        f.write('''
tigmint-cut --processes 8 --window 1000 --spanning 2 --trim 0 --fastaout {0}/03.tigmint/draft.tigmint.fa {0}/03.tigmint/draft.fa {0}/03.tigmint/draft.reads.molecule.bed
'''.format(work_dir,**config['args']))

def tigmint_molecular(config):
    work_dir = config['general']['work_dir']
    with open(work_dir + '/05.script/tigmint_molecular.sh', 'a') as f:
        f.write('''#!/usr/bin/env bash
export PATH={tigmint}:$PATH

cd {work_dir}/03.tigmint
'''.format(**config['general']))
        f.write('''
tigmint-molecule --dist 50000 --reads 4 --mapq 0 --as-ratio 0.65 --nm 5 --size 2000 {0}/03.tigmint/draft.reads.sortbx.bam | sort -k1,1 -k2,2n -k3,3n > {0}/03.tigmint/draft.reads.molecule.bed
'''.format(work_dir, **config['args']))

def main():
    # 读取cfg
    work_dir = sys.argv[1]
    config = CaseConfigParser()
    config.read(work_dir + '/env.cfg')
    config.sections()
    config.set('general', 'work_dir', work_dir)

    # 创建文件夹
    if not os.path.exists(work_dir + '/00.reads'):
        os.makedirs(work_dir + '/00.reads')
    if not os.path.exists(work_dir + '/01.mapping'):
        os.makedirs(work_dir + '/01.mapping')
    if not os.path.exists(work_dir + '/02.basic'):
        os.makedirs(work_dir + '/02.basic')
    if not os.path.exists(work_dir + '/03.tigmint'):
        os.makedirs(work_dir + '/03.tigmint')
    if not os.path.exists(work_dir + '/04.log'):
        os.makedirs(work_dir + '/04.log')
    if not os.path.exists(work_dir + '/05.script'):
        os.makedirs(work_dir + '/05.script')

    # 软链reads,fqs记录reads的原始路径
    fqs = []
    for fq in os.listdir(config['general']['reads']):
        if fq.endswith('gz'):
            fqs.append(config['general']['reads'] + '/' + fq)
    fqs.sort()
    mapping_nums = int(len(fqs) / 2)
    if len(os.listdir(work_dir + '/00.reads')) == 0:
        for i in range(mapping_nums):
            os.mkdir(work_dir + '/00.reads/' + str(i))
            os.symlink(fqs[2 * i], '/'.join([work_dir + '00.reads' + str(i) + 'XG_S1_L001_R1_001.fastq.gz']))
            os.symlink(fqs[2 * i + 1], '/'.join([work_dir + '00.reads' + str(i) + 'XG_S1_L001_R2_001.fastq.gz']))
    if not os.path.exists(work_dir+'03.tigmint/draft.fa'):
        os.symlink(config['general']['contig'],'/'.join([work_dir + '03.tigmint' + 'draft.fa']))
    if mapping_nums == 0:
        mapping_nums = len(os.listdir(work_dir + '/00.reads'))
    config.set('general', 'mapping_nums', str(mapping_nums))


    # longranger basic
    config = longranger(config)

    # mapping,bwa
    config = mapping(config)

    # tigmint_cut
    config = tigmint_cut(config)

    # tigmint_molecular
    config = tigmint_molecule(config)


if __name__ == "__main__":
    main()
