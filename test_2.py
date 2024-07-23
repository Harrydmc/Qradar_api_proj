import requests
import json
import datetime

# QRadar API details
api_url = "https://192.168.0.111/"
api_token = "1fcf78e9-4521-4e37-9254-7b34dd3dd936"
headers = {"Content-Type": "application/json", "SEC": api_token}

# Function to get all log sources
def get_log_sources():
    url = f"{api_url}api/config/event_sources/log_source_management/log_sources"
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching log sources: {e}")
        return None

# Function to get event collectors
def get_event_collectors():
    url = f"{api_url}api/config/event_sources/event_collectors"
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching event collectors: {e}")
        return None

# Function to get log source types
def get_log_source_types():
    url = f"{api_url}api/config/event_sources/log_source_management/log_source_types"
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching log source types: {e}")
        return None

# Function to format timestamp
def format_timestamp(timestamp):
    if timestamp:
        return datetime.datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
    return 'N/A'

# Function to search log sources by name
def search_log_sources(search_name):
    log_sources = get_log_sources()
    if log_sources:
        matching_log_sources = [ls for ls in log_sources if ls.get('enabled') and search_name.lower() in ls.get("name", "").lower()]
        return matching_log_sources
    return None

# Function to count devices reporting to the same collector
def count_devices_for_collector(target_collector_id, log_sources):
    count = 0
    for log_source in log_sources:
        if log_source.get('enabled') and log_source.get('target_event_collector_id') == target_collector_id:
            count += 1
    return count

# Function to get log source type name
def get_log_source_type_name(type_id, log_source_types):
    for log_source_type in log_source_types:
        if log_source_type.get('id') == type_id:
            return log_source_type.get('name', 'Unknown')
    return 'Unknown'

# Static search name
search_name = "TEST_1"

# Main script
if __name__ == "__main__":
    print(f"Searching for log sources with name: {search_name}")

    log_sources = get_log_sources()
    if not log_sources:
        print(f"No log sources found.")
    else:
        matching_log_sources = search_log_sources(search_name)
        if not matching_log_sources:
            print(f"No log sources found with name: {search_name}")
        else:
            event_collectors = get_event_collectors()
            log_source_types = get_log_source_types()

            for log_source in matching_log_sources:
                collector_id = log_source.get('target_event_collector_id')
                collector_name = next((ec.get('name') for ec in event_collectors if ec.get('id') == collector_id), 'Unknown') if event_collectors else 'Unknown'
                log_source_type_name = get_log_source_type_name(log_source.get('type_id'), log_source_types) if log_source_types else 'Unknown'
                devices_count = count_devices_for_collector(collector_id, log_sources)

                print(f"\nLog Source Name: {log_source.get('name', 'N/A')}")
                print(f"Log Source Type: {log_source_type_name}")
                print(f"Last Event Time: {format_timestamp(log_source.get('last_event_time'))}")
                print(f"Target Event Collector: {collector_name}")
                print(f"Number of Devices Reporting to Collector: {devices_count}")
