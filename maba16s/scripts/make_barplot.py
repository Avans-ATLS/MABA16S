import os
import argparse
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt

def convert_xlsx_to_csv(input_folder, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file_name in os.listdir(input_folder):
        if file_name.endswith(".xlsx"):
            input_file_path = os.path.join(input_folder, file_name)
            output_file_path = os.path.join(output_folder, file_name.replace(".xlsx", ".csv"))
            convert_file_to_csv(input_file_path, output_file_path)

def convert_file_to_csv(input_file_path, output_file_path):
    # Read Excel file and write to CSV
    data = pd.read_excel(input_file_path)
    data.to_csv(output_file_path, index=False)

def process_csv_files(input_folder, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file_name in os.listdir(input_folder):
        if file_name.endswith(".csv"):
            input_file_path = os.path.join(input_folder, file_name)
            output_file_path = os.path.join(output_folder, file_name)
            process_csv_file(input_file_path, output_file_path)

def process_csv_file(input_file_path, output_file_path):
    # Read CSV file and select only 'blast_hit' and 'num_reads' columns
    data = pd.read_csv(input_file_path)
    selected_columns = ['blast_hit', 'num_reads']
    processed_data = data[selected_columns]
    processed_data.to_csv(output_file_path, index=False)

def merge_csv_files(input_folder, output_file):
    all_data = []

    # Iterate over all CSV files in the input folder
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".csv"):
            barcode = os.path.splitext(file_name)[0]  # Extract barcode from file name
            input_file_path = os.path.join(input_folder, file_name)
            data = pd.read_csv(input_file_path)
            data['Barcode'] = barcode  # Add a 'Barcode' column to identify the source
            all_data.append(data)

    # Concatenate all dataframes into one
    merged_data = pd.concat(all_data, ignore_index=True)

    # Save the merged dataframe to a CSV file
    merged_data.to_csv(output_file, index=False)

def plot_stacked_bar(input_csv, output_html, output_csv):
    # Read input CSV
    df = pd.read_csv(input_csv)

    # Consolidate data for each species within each barcode
    df_consolidated = df.groupby(['Barcode', 'blast_hit']).agg({'num_reads': 'sum'}).reset_index()

    # Calculate total reads for each barcode
    df_consolidated['Total_reads'] = df_consolidated.groupby('Barcode')['num_reads'].transform('sum')

    # Calculate percentage of reads for each species in each barcode
    df_consolidated['Percentage'] = (df_consolidated['num_reads'] / df_consolidated['Total_reads']) * 100

    # Round percentage to 2 decimals
    df_consolidated['Percentage'] = df_consolidated['Percentage'].round(2)

    # Aggregate species with <= 1% abundance into 'Other species <1%'
    df_consolidated.loc[df_consolidated['Percentage'] <= 1, 'blast_hit'] = 'Other species <1%'
    df_consolidated = df_consolidated.groupby(['Barcode', 'blast_hit']).sum().reset_index()

    # Create a dictionary to map species to colors
    species_colors = {}
    species_list = df_consolidated['blast_hit'].unique()
    color_palette = px.colors.qualitative.Plotly
    for i, species in enumerate(species_list):
        species_colors[species] = color_palette[i % len(color_palette)]

    # Create traces for each species
    traces = []
    for species in species_list:
        species_df = df_consolidated[df_consolidated['blast_hit'] == species]
        traces.append(go.Bar(x=species_df['Barcode'], y=species_df['Percentage'], name=species, marker_color=species_colors[species]))

    # Create layout
    layout = go.Layout(title='Stacked Bar Plot of Species Percentage per Barcode',
                       xaxis_title='Barcode',
                       yaxis_title='Percentage of Reads',
                       barmode='stack')

    # Create figure
    fig = go.Figure(data=traces, layout=layout)

    # Save the plot as HTML
    fig.write_html(output_html)

    # Save the percentages of each species to a CSV file
    df_consolidated.to_csv(output_csv, index=False, float_format='%.2f')

def main(input_folder, output_folder):
    # Convert .xlsx files to .csv files
    converted_folder = os.path.join(output_folder, "converted_csv")
    convert_xlsx_to_csv(input_folder, converted_folder)

    # Process .csv files
    processed_folder = os.path.join(output_folder, "processed_csv")
    process_csv_files(converted_folder, processed_folder)

    # Merge processed .csv files into one
    merged_file = os.path.join(output_folder, "merged_data.csv")
    merge_csv_files(processed_folder, merged_file)

    # Plot stacked bar plot
    plot_output_file = os.path.join(output_folder, "stacked_bar_plot.html")
    plot_csv_file = os.path.join(output_folder, "species_percentages.csv")
    plot_stacked_bar(merged_file, plot_output_file, plot_csv_file)


def plot_boolean_forest(pa: dict[str, bool], outpath: str):
    # set up plot layout
    num_samples = len(pa)
    cols = 4
    rows = (num_samples + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2, rows * 2))
    axes = axes.flatten()

    # plot each sample
    for i, (key, value) in enumerate(pa.items()):
        ax = axes[i]
        ax.set_title(key)
        ax.set_xticks([])
        ax.set_yticks([])

        if value:
            circle = plt.Circle((0.5, 0.5), 0.4, color='green', ec='black', lw=2)
            ax.text(0.5, 0.5, 'Dominant', ha='center', va='center', fontsize=12)
        else:
            circle = plt.Circle((0.5, 0.5), 0.4, color='cyan', ec='black', lw=2)
            ax.text(0.5, 0.5, 'Niet dominant', ha='center', va='center', fontsize=12)
        
        ax.add_patch(circle)
    
    # remove empty subplots
    for i in range(num_samples, rows * cols):
        fig.delaxes(axes[i])
    
    plt.tight_layout()
    plt.savefig(outpath)

def crispatus_presence_absence(input_csv, outdir):
    pa = {}
    df = pd.read_csv(input_csv)
    for bc in df['Barcode'].unique():
        if 'Lactobacillus crispatus' in df[df['Barcode'] == bc]['blast_hit'].unique():
            percentage = df[df['Barcode'] == bc][df[df['Barcode'] == bc]['blast_hit'] == 'Lactobacillus crispatus']['Percentage'].values[0]
            if percentage > 60:
                pa[bc] = True
            else: 
                pa[bc] = False
    plot_boolean_forest(pa, os.path.join(outdir, 'crispatus_presence_absence.png'))
