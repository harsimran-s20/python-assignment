import pandas as pd
import os
import glob
import math

def find_csv_files(folder_path):
    """
    Finds all CSV files within the specified folder.

    Args:
        folder_path (str): The path to the folder containing CSV files.

    Returns:
        list: A list of file paths for the CSV files found.
    """
    pattern = os.path.join(folder_path, "*.csv")
    csv_files = glob.glob(pattern)
    return csv_files

def process_data(csv_files):
    """
    Processes all temperature CSV files (monthly data) to calculate seasonal averages,
    largest temperature range, and temperature stability.

    Args:
        csv_files (list): A list of paths to CSV files.

    Returns:
        tuple: A tuple containing:
            - dict: Seasonal averages (e.g., {'Summer': 25.1}).
            - dict: Largest temp range info ({'min_station': ..., 'max_station': ..., 'min_temp': ..., 'max_temp': ...}).
            - dict: Stability info ({'most_stable': [...], 'most_variable': [...], 'details': {...}}).
    """
    if not csv_files:
        print("No CSV files found to process.")
        return {}, {}, {}

    # --- Initialization ---
    seasonal_sums = {'Summer': 0.0, 'Autumn': 0.0, 'Winter': 0.0, 'Spring': 0.0}
    seasonal_counts = {'Summer': 0, 'Autumn': 0, 'Winter': 0, 'Spring': 0}
    
    # Storing all temperatures for each station for std dev calculation
    station_temps = {}  # {'StationID': [temp1, temp2, ...]}

    # Australian seasons based on month names (from CSV columns)
    australian_seasons = {
        'December': 'Summer', 'January': 'Summer', 'February': 'Summer',
        'March': 'Autumn', 'April': 'Autumn', 'May': 'Autumn',
        'June': 'Winter', 'July': 'Winter', 'August': 'Winter',
        'September': 'Spring', 'October': 'Spring', 'November': 'Spring'
    }
    
    # Initializing variables for tracking the largest range across all data
    overall_min_temp = float('inf')
    overall_max_temp = float('-inf')
    min_temp_station_id = None
    max_temp_station_id = None

    # --- Main Processing Loop ---
    for file_path in csv_files:
        try:
            # Reading the CSV file
            df = pd.read_csv(file_path)
            
            # Iterating through each row (which represents a station)
            for index, row in df.iterrows():
                station_id = row['STN_ID'] # Using STN_ID for identification
                station_name = row['STATION_NAME'] # Could be used for reporting
                
                # Initializing temperature list for this station if not already
                if station_id not in station_temps:
                    station_temps[station_id] = []

                # Iterating through the month columns (January to December)
                for month_name in australian_seasons.keys():
                    temperature = row[month_name]
                    
                    # Checking if the temperature value is a valid number
                    if pd.notna(temperature) and isinstance(temperature, (int, float)) and not math.isnan(temperature):
                        
                        # --- 1. Seasonal Averages ---
                        season = australian_seasons.get(month_name)
                        if season:
                            seasonal_sums[season] += temperature
                            seasonal_counts[season] += 1

                        # --- 2. Temperature Range (Global Min/Max) ---
                        if temperature < overall_min_temp:
                            overall_min_temp = temperature
                            min_temp_station_id = station_id
                        if temperature > overall_max_temp:
                            overall_max_temp = temperature
                            max_temp_station_id = station_id

                        # --- 3. Stability (Collect temps per station) ---
                        station_temps[station_id].append(temperature)

        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            continue # Continuing with the next file

    # --- Post-Processing Calculations ---
    
    # 1. Calculating Seasonal Averages
    seasonal_averages = {}
    for season in seasonal_sums:
        if seasonal_counts[season] > 0:
            seasonal_averages[season] = seasonal_sums[season] / seasonal_counts[season]
        else:
            seasonal_averages[season] = None # Indicating no data for this season

    # 2. Determining Largest Temperature Range Info
    largest_range_info = {
        'min_station': min_temp_station_id,
        'max_station': max_temp_station_id,
        'min_temp': overall_min_temp if overall_min_temp != float('inf') else None,
        'max_temp': overall_max_temp if overall_max_temp != float('-inf') else None
    }
    if largest_range_info['min_temp'] is not None and largest_range_info['max_temp'] is not None:
        largest_range_info['range'] = largest_range_info['max_temp'] - largest_range_info['min_temp']
    else:
        largest_range_info['range'] = None


    # 3. Finding Temperature Stability (Standard Deviation)
    stability_info = {'most_stable': [], 'most_variable': [], 'details': {}}
    standard_deviations = {}
    
    for station_id, temps in station_temps.items():
        if temps: # Checking if list is not empty
            std_dev = pd.Series(temps).std()
            if not pd.isna(std_dev): # Checking if std dev is valid
                standard_deviations[station_id] = std_dev
        # else: std dev is undefined for stations with no data

    if standard_deviations:
        min_std = min(standard_deviations.values())
        max_std = max(standard_deviations.values())

        for station_id, std_dev in standard_deviations.items():
            stability_info['details'][station_id] = std_dev
            # Using math.isclose for safe float comparison in case of ties
            if math.isclose(std_dev, min_std, rel_tol=1e-9):
                stability_info['most_stable'].append(station_id)
            if math.isclose(std_dev, max_std, rel_tol=1e-9):
                stability_info['most_variable'].append(station_id)
    else:
        print("Warning: No valid temperature data found for stability calculation.")

    return seasonal_averages, largest_range_info, stability_info

def write_averages(averages, filename):
    """
    Writes the calculated seasonal averages to a file.

    Args:
        averages (dict): Dictionary of seasonal averages.
        filename (str): The name of the output file.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for season in ['Summer', 'Autumn', 'Winter', 'Spring']:
                avg_temp = averages.get(season)
                if avg_temp is not None:
                    f.write(f"{season}: {avg_temp:.1f}°C\n")
                else:
                    f.write(f"{season}: No data\n")
        print(f"Seasonal averages written to '{filename}'.")
    except IOError as e:
        print(f"Error writing to '{filename}': {e}")

def write_largest_range(largest_range_info, filename):
    """
    Writes the station(s) with the largest temperature range to a file.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            min_station = largest_range_info.get('min_station')
            max_station = largest_range_info.get('max_station')
            min_temp = largest_range_info.get('min_temp')
            max_temp = largest_range_info.get('max_temp')
            temp_range = largest_range_info.get('range')

            if temp_range is None or min_temp is None or max_temp is None:
                f.write("No temperature data available to determine range.\n")
            else:                
                f.write(f"Global Range: {temp_range:.1f}°C (Max: {max_temp:.1f}°C at Station {max_station}, Min: {min_temp:.1f}°C at Station {min_station})\n")
                
        print(f"Largest temperature range info written to '{filename}'.")
    except IOError as e:
        print(f"Error writing to '{filename}': {e}")

def write_stability(stability_info, filename):
    """
    Writes the most stable and most variable stations to a file.

    Args:
        stability_info (dict): Info about station stability.
        filename (str): The name of the output file.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            most_stable = stability_info.get('most_stable', [])
            most_variable = stability_info.get('most_variable', [])
            details = stability_info.get('details', {})
            
            if not most_stable or all(sid not in details or pd.isna(details[sid]) for sid in most_stable):
                f.write("Most Stable: No data\n")
            else:
                # Reporting the first one
                first_stable_id = most_stable[0]
                std_dev = details.get(first_stable_id, float('inf'))
                f.write(f"Most Stable: Station {first_stable_id}: StdDev {std_dev:.1f}°C")
                if len(most_stable) > 1:
                     f.write(f" (Tied with {len(most_stable) - 1} other station(s))")
                f.write("\n")
            
            if not most_variable or all(sid not in details or pd.isna(details[sid]) for sid in most_variable):
                f.write("Most Variable: No data\n")
            else:
                first_variable_id = most_variable[0]
                std_dev = details.get(first_variable_id, 0)
                f.write(f"Most Variable: Station {first_variable_id}: StdDev {std_dev:.1f}°C")
                if len(most_variable) > 1:
                     f.write(f" (Tied with {len(most_variable) - 1} other station(s))")
                f.write("\n")
                
        print(f"Temperature stability info written to '{filename}'.")
    except IOError as e:
        print(f"Error writing to '{filename}': {e}")

def main():
    """
    Main function to orchestrate the temperature data analysis.
    """
    print("--- Temperature Data Analysis (Corrected) ---")
    data_folder = "temperatures" # Making sure this folder exists and contains the CSVs
    
    if not os.path.exists(data_folder):
        print(f"Error: Data folder '{data_folder}' not found.")
        return

    csv_files = find_csv_files(data_folder)
    
    if not csv_files:
        print(f"No CSV files found in '{data_folder}'.")
        return

    print(f"Found {len(csv_files)} CSV file(s) to process.")
    
    # Processing the data
    averages, largest_range, stability = process_data(csv_files)

    # Writing outputs
    write_averages(averages, "average_temp.txt")
    write_largest_range(largest_range, "largest_temp_range_station.txt")
    write_stability(stability, "temperature_stability_stations.txt")
    
    print("--- Analysis Complete ---")

if __name__ == "__main__":
    main()