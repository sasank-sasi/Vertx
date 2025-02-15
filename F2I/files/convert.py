import pandas as pd

def excel_to_csv(excel_file, output_dir):
    # Read the Excel file
    df = pd.read_excel(excel_file, sheet_name=None)  # Read all sheets

    # Save each sheet to a separate CSV file
    for sheet_name, data in df.items():
        csv_file = f"{output_dir}/{sheet_name}.csv"
        data.to_csv(csv_file, index=False)
        print(f"CSV file saved as {csv_file}")

# Example usage
excel_to_csv("Investors200.xlsx", "/Users/sasanksasi/Downloads/project/VertexAi")