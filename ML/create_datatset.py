import pandas as pd
import os
import re

def merge_tsv_files(directory='C:\\Users\\harsh\\OneDrive\\Desktop\\MajorProject\\ML'):
    """
    Merge all TSV files (keystrokes, mouse_mov_speeds, usercondition) into one CSV file.
    No aggregation, just concatenation of all rows from all files.
    """
    # Find all TSV files in the directory
    files = [f for f in os.listdir(directory) if f.endswith('.tsv')]
    
    # These are the 6 specific files we're looking for
    expected_files = [
        # 'keystrokes1.tsv', 'keystrokes2.tsv',
        # 'mouse_mov_speeds1.tsv', 'mouse_mov_speeds2.tsv',
        'usercondition1.tsv', 'usercondition2.tsv'
    ]
    
    # Filter to only include our 6 specific files (if they're in the directory)
    files_to_process = [f for f in files if f in expected_files]
    
    if not files_to_process:
        print("None of the expected TSV files found in the directory.")
        return
    
    print(f"Found {len(files_to_process)} of the 6 expected TSV files to merge.")
    
    # Initialize an empty list to store all dataframes
    all_dfs = []
    
    # Process each file
    for filename in files_to_process:
        try:
            file_path = os.path.join(directory, filename)
            print(f"Processing {filename}...")
            
            # Extract session ID to add as a column
            match = re.search(r'(\d+)\.tsv$', filename)
            session_id = match.group(1) if match else '0'
            
            # Extract file type (keystrokes, mouse_mov_speeds, usercondition)
            file_type = re.sub(r'\d+\.tsv$', '', filename)
            
            # Load the TSV file
            df = pd.read_csv(file_path, sep='\t')
            
            # Add columns to identify the source file
            df['SourceFile'] = filename
            df['SessionID'] = session_id
            df['DataType'] = file_type
            
            # Add to our list of dataframes
            all_dfs.append(df)
            
            print(f"  Added {len(df)} rows from {filename}")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    # Concatenate all dataframes
    if all_dfs:
        merged_df = pd.concat(all_dfs, ignore_index=True)
        
        # Save to CSV
        output_file = 'usercondition_combined.csv'
        merged_df.to_csv(output_file, index=False)
        
        print(f"\nSuccessfully merged all data into {output_file}")
        print(f"Total rows in merged file: {len(merged_df)}")
        print(f"Columns in merged file: {', '.join(merged_df.columns)}")
        
        return merged_df
    else:
        print("No files were successfully processed.")
        return None

if __name__ == "__main__":
    # Merge all TSV files in the current directory
    merged_data = merge_tsv_files()
    
    # Display the first few rows of the merged dataset
    if merged_data is not None:
        print("\nFirst few rows of the merged dataset:")
        print(merged_data.head())