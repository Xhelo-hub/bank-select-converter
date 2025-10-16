#!/usr/bin/env python3
"""
MERGE-CSV-BULK.py
=================

Bulk CSV file merger utility for bank statements.
This script merges multiple CSV files from the export folder,
sorting transactions from oldest to newest.

Author: Generated for QuickBooks CSV processing
Date: October 5, 2025
"""

import csv
import os
from pathlib import Path
from datetime import datetime
import re

def parse_date(date_str):
    """Parse date string in various formats and return datetime object."""
    # Common date formats to try
    date_formats = [
        '%d/%m/%Y',     # 31/12/2023
        '%d.%m.%Y',     # 31.12.2023
        '%Y-%m-%d',     # 2023-12-31
        '%m/%d/%Y',     # 12/31/2023
        '%d-%m-%Y',     # 31-12-2023
        '%Y/%m/%d',     # 2023/12/31
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except (ValueError, TypeError):
            continue
    
    # If no format works, return None
    return None

def find_date_column(headers, first_row):
    """Find the column that contains dates."""
    date_keywords = ['date', 'data', 'datum', 'fecha', 'transaction date', 'trans date']
    
    # First, try to find by column name
    for i, header in enumerate(headers):
        if any(keyword in header.lower() for keyword in date_keywords):
            return i
    
    # If not found by name, try to find by content
    for i, value in enumerate(first_row):
        try:
            if parse_date(value) is not None:
                return i
        except:
            continue
    
    return None

def get_next_filename(export_folder, base_name):
    """Generate filename with incremental number if file exists."""
    filename = f"{base_name}.csv"
    filepath = export_folder / filename
    
    if not filepath.exists():
        return filepath
    
    # File exists, find next available number
    counter = 1
    while True:
        filename = f"{base_name} ({counter}).csv"
        filepath = export_folder / filename
        if not filepath.exists():
            return filepath
        counter += 1

def read_csv_file(file_path):
    """Read CSV file and return headers and rows."""
    rows = []
    headers = []
    
    # Common delimiters to try
    delimiters = [',', ';', '\t', '|']
    
    for encoding in ['utf-8', 'cp1252', 'iso-8859-1']:
        for delimiter in delimiters:
            try:
                with open(file_path, 'r', encoding=encoding, newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=delimiter)
                    headers = next(reader)  # First row as headers
                    rows = list(reader)
                    
                    # Check if this seems like a valid CSV (headers should have multiple columns)
                    if len(headers) > 1:
                        return headers, rows
                        
            except (UnicodeDecodeError, StopIteration, csv.Error):
                continue
    
    # If all else fails, try to auto-detect
    try:
        with open(file_path, 'r', encoding='utf-8', newline='') as csvfile:
            # Read a sample to detect delimiter
            sample = csvfile.read(2048)
            csvfile.seek(0)
            
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample, delimiters=',;\t|').delimiter
            
            reader = csv.reader(csvfile, delimiter=delimiter)
            headers = next(reader)
            rows = list(reader)
            
    except Exception as e:
        raise Exception(f"Could not read CSV file: {str(e)}")
    
    return headers, rows

def main():
    print("=" * 80)
    print("CSV BULK MERGER - Bank Statement Consolidator")
    print("=" * 80)
    print()
    
    # Search in current directory and import folder
    search_paths = [Path.cwd(), Path.cwd() / "import"]
    all_csv_files = []
    
    for search_path in search_paths:
        if search_path.exists():
            all_csv_files.extend(list(search_path.glob("*.csv")))
    csv_files = []
    
    # Filter out files that contain "Merged" in the name
    for csv_file in all_csv_files:
        if "merged" not in csv_file.name.lower():
            csv_files.append(csv_file)
        else:
            print(f"🔄 Skipping previously merged file: {csv_file.name}")
    
    if not csv_files:
        print(f"❌ No original CSV files found in current directory")
        print("(Files containing 'Merged' in the name are excluded)")
        return
    
    print(f"📁 Found {len(csv_files)} original CSV file(s) to merge:")
    for csv_file in csv_files:
        print(f"   - {csv_file.name}")
    print()
    
    # Read and combine all CSV files
    file_data = []  # List to store (file_info, headers, rows) tuples
    common_headers = None
    total_rows = 0
    
    for csv_file in csv_files:
        try:
            print(f"📖 Reading: {csv_file.name}")
            headers, rows = read_csv_file(csv_file)
            
            if not rows:
                print(f"   ⚠️  File is empty, skipping...")
                continue
            
            # Set headers from first file
            if common_headers is None:
                common_headers = headers
                # Find date column from first file
                date_column_index = find_date_column(headers, rows[0] if rows else [])
                if date_column_index is not None:
                    print(f"   📅 Found date column: '{headers[date_column_index]}' (column {date_column_index + 1})")
            
            # Find the oldest date in this file for sorting files
            oldest_date = None
            for row in rows:
                if date_column_index is not None and date_column_index < len(row):
                    parsed_date = parse_date(row[date_column_index])
                    if parsed_date:
                        if oldest_date is None or parsed_date < oldest_date:
                            oldest_date = parsed_date
            
            # Store file data with its oldest date for sorting
            file_data.append({
                'filename': csv_file.name,
                'oldest_date': oldest_date or datetime.max,  # Use max date if no valid date found
                'headers': headers,
                'rows': rows
            })
            
            total_rows += len(rows)
            print(f"   ✓ Loaded {len(rows)} rows")
            if oldest_date:
                print(f"   📅 Oldest transaction: {oldest_date.strftime('%d/%m/%Y')}")
            
        except Exception as e:
            print(f"   ❌ Error reading {csv_file.name}: {str(e)}")
            continue
    
    if not file_data:
        print("❌ No valid CSV files could be processed.")
        return
    
    print(f"\n📊 Total rows to merge: {total_rows}")
    
    # Sort files by their oldest transaction date (files with earliest dates first)
    print("🔄 Ordering files by oldest transaction date...")
    file_data.sort(key=lambda x: x['oldest_date'])
    
    print("📋 File processing order:")
    for i, file_info in enumerate(file_data, 1):
        oldest_str = file_info['oldest_date'].strftime('%d/%m/%Y') if file_info['oldest_date'] != datetime.max else "No valid dates"
        print(f"   {i}. {file_info['filename']} (oldest: {oldest_str})")
    print()
    
    # Combine all rows in file order (keeping each file's data together)
    all_rows = []
    for file_info in file_data:
        print(f"📝 Adding {len(file_info['rows'])} rows from {file_info['filename']}")
        all_rows.extend(file_info['rows'])
    
    # Generate output filename - save in export folder
    export_folder = Path("export")
    export_folder.mkdir(exist_ok=True)
    output_file = get_next_filename(export_folder, "Bank Statement - Merged")
    
    # Save merged data
    print(f"💾 Saving merged data to: {output_file.name}")
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(common_headers)  # Write headers
            writer.writerows(all_rows)       # Write all data rows
        
        print(f"   ✓ Successfully saved {len(all_rows)} rows")
        print(f"   📄 File location: {output_file}")
        
        # Show summary
        print(f"\n📋 MERGE SUMMARY:")
        print(f"   • Original files processed: {len(file_data)}")
        print(f"   • Total transactions: {len(all_rows)}")
        print(f"   • Output file: {output_file.name}")
        print(f"   • Files ordered by oldest transaction date (data kept together per file)")
        
        # Show file order summary
        print(f"\n📄 File processing order:")
        for i, file_info in enumerate(file_data, 1):
            oldest_str = file_info['oldest_date'].strftime('%d/%m/%Y') if file_info['oldest_date'] != datetime.max else "No dates"
            print(f"   {i}. {file_info['filename']} ({len(file_info['rows'])} rows, oldest: {oldest_str})")
        
    except Exception as e:
        print(f"   ❌ Error saving file: {str(e)}")
        return
    
    print("\n✅ Merge completed successfully!")

if __name__ == "__main__":
    main()