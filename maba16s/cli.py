#!/usr/bin/env python3

import sys
from argparse import ArgumentParser
import yaml
import os
from scripts.renamer import renamer
from scripts import make_barplot

locationrepo = os.path.dirname(os.path.abspath(__file__))


def get_absolute_path(path):
    return os.path.abspath(path)


def file_name_generator(filepath):
    return os.path.splitext(os.path.basename(filepath))[0]


def snakemake_in(samples,  outdir, ):
    samplesdic = {}
    samplesdic['parameters'] = {}
    samplesdic['parameters']["outdir"] = get_absolute_path(outdir)
    samplesdic["SAMPLES"] = {}

    # generate the samples dictionary as input for snakemake
    for i in samples:
        samplename = file_name_generator(i)
        samplesdic["SAMPLES"][samplename] = get_absolute_path(i)
    data = yaml.dump(samplesdic, default_flow_style=False)

    # make and write config file location
    os.system(f"mkdir -p {locationrepo}/config")
    with open(f"{locationrepo}/config/config.yaml", 'w') as f:
        f.write(data)


def main(command_line=None):
    """Console script for MABA16S."""
    # add main parser object
    parser = ArgumentParser(description="Maastricht Bacterial 16S workflow")

    # add sub parser object
    subparsers = parser.add_subparsers(dest="mode")

    # add module rename barcodes to samples
    rename = subparsers.add_parser(
            "rename",
            help="""rename barcode.fasta to
            samplenames supplied in a spreadsheet""")

    rename.add_argument("-i",
                        required=True,
                        dest='input_directory',

                        )
    rename.add_argument("--spreadsheet",
                        required=True,
                        dest='spreadsheet',
                        help='supply a spreadsheet to rename samples'
                        )

    # add snakemake pipeline to completely run fasta to 16S report
    snakemake = subparsers.add_parser("snakemake",
                                      help='''run the entire workflow on 16S
                                      sequenced samples''')
    snakemake.add_argument(
                "-i",
                required=True,
                dest="input_files",
                nargs="+"
                )
    snakemake.add_argument(
                            "--cores",
                            dest='cores',
                            required=True,
                            type=int,
                            help='Number of CPU cores to use'
                            )

    snakemake.add_argument("-o", required=True, dest="outdir")

    snakemake.add_argument(
                            "--snakemake-params",
                            required=False,
                            dest="smkparams",
                            )

####################
# parsing part
####################

    args = parser.parse_args(command_line)
    if args.mode == "rename":
        renamer(
                barcode_dir=args.input_directory,
                metadata=args.spreadsheet
                )

    elif args.mode == "snakemake":
        snakemake_in(
                samples=args.input_files,
                outdir=os.path.abspath(args.outdir),
                )
        outdir = os.path.abspath(args.outdir)
        os.chdir(f"{locationrepo}")

        if args.smkparams == None:
            args.smkparams=""
        exitstatus = os.system(f"snakemake --cores {args.cores} --use-conda {args.smkparams} --snakefile Snakefile_check_suitable_samples.smk")
        if exitstatus > 0:
            sys.exit("pre-workflow crashed")
        os.system(f"snakemake -p --cores {args.cores} --use-conda {args.smkparams} --notemp --keep-going")
        xlsxdir = os.path.join(outdir, 'reports')
        make_barplot.main(xlsxdir, outdir)
        make_barplot.crispatus_presence_absence(os.path.join(outdir, 'species_percentages.csv'), outdir)
        

    else:
        parser.print_usage()
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
