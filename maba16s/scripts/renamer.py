import pandas as pd
import os

BARCODE_DIR = '/home/sander/Lowlands/datasets/testrun/fastq_pass'
METADATA = '/home/sander/Lowlands/sample_sheets/dummy.txt'

def renamer(barcode_dir: str, metadata: str):
    meta = pd.read_csv(metadata, sep='\t', header=0, index_col=0).to_dict()['SampleID']
    for bc, id in meta.items():
        if os.path.exists(os.path.join(barcode_dir, bc)):
            os.rename(os.path.join(barcode_dir, bc), os.path.join(barcode_dir, id))
        
        else:
            print(f'Directory {os.path.abspath(os.path.join(barcode_dir, bc))} not found for sample {id}')

    