#!/usr/bin/env python3
"""
Extract frame and elemental_id columns from CSV using pandas.
"""

import pandas as pd
import sys
import os

def extract_columns(input_file, output_file=None):
    """
    Extract frame and elemental_id columns from CSV using pandas.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (optional)
    
    Returns:
        Path to output file
    """
    # Generate output filename if not provided
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_cleaned{ext}"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    
    try:
        # Read CSV file
        df = pd.read_csv(input_file)
        
        # Check if required columns exist
        required_cols = {'frame', 'uuid'}
        missing_cols = required_cols - set(df.columns)
        
        if missing_cols:
            print(f"Error: Missing required columns: {missing_cols}")
            print(f"Available columns: {list(df.columns)}")
            sys.exit(1)
        
        # Select only the required columns
        df_clean = df[['frame', 'uuid']].copy()

        # Subtract 1 keeping from negative
        df_clean['frame'] = (df_clean['frame'] - 1).clip(lower=0)

        # Remove rows with missing values
        initial_count = len(df_clean)
        df_clean = df_clean.dropna(subset=['frame', 'uuid'])
        rows_removed = initial_count - len(df_clean)
       
        df_clean = df_clean.rename(columns={'uuid': 'elemental_id'})

        if rows_removed > 0:
            print(f"Note: Removed {rows_removed} rows with missing values")
        
        # Save to new CSV
        df_clean.to_csv(output_file, index=False)
        
        print(f"Successfully extracted {len(df_clean)} rows")
        print(f"Output saved to: {output_file}")
        
        # Display summary
        print(f"\nSummary:")
        print(f"  Frame range: {int(df_clean['frame'].min())} to {int(df_clean['frame'].max())}")
        print(f"  Unique UUIDs: {df_clean['elemental_id'].nunique()}")
        
        return output_file
        
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)

def main():
    """Main function with command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract frame and elemental_id columns from CSV using pandas.'
    )
    parser.add_argument('input', help='Input CSV file path')
    parser.add_argument('-o', '--output', help='Output CSV file path (optional)')
    
    args = parser.parse_args()
    
    extract_columns(args.input, args.output)

if __name__ == '__main__':
    main()
