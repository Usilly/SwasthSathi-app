import pandas as pd

# IMPORTANT: Replace this with the actual name of your large file
large_filename = 'final.csv'
# This will be the name of our new, smaller file
output_filename = 'symptom_data_clean.csv'

print(f"Loading the large dataset: {large_filename}...")

try:
    # Load the entire dataset
    df = pd.read_csv(large_filename)

    print("Dataset loaded successfully. It has {} rows.".format(len(df)))

    # --- Data Cleaning and Reduction ---

    # 1. Remove duplicate rows, if any
    df.drop_duplicates(inplace=True)
    print("Removed duplicate rows. It now has {} rows.".format(len(df)))

    # 2. (Optional) If there are unnecessary columns, you can drop them here.
    # For example, if there was a column named 'patient_id', you could use:
    # df = df.drop('patient_id', axis=1)

    # --- Saving the new file ---
    df.to_csv(output_filename, index=False)

    print("\nSUCCESS! ✅")
    print(f"A new, smaller file has been created: '{output_filename}'")
    print("Please use this new file for the SwasthSathi application.")

except FileNotFoundError:
    print(f"\nERROR: The file '{large_filename}' was not found.")
    print("Please make sure it's in the same folder as this script.")
except Exception as e:
    print(f"\nAn error occurred: {e}")