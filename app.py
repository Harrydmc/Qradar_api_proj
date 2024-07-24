from flask import Flask, request, render_template
import requests
import json
import datetime
import pytz

app = Flask(__name__)

# Dictionary to store QRadar consoles
qradar_consoles = {
    "qradar_1": {
        "api_url": "https://192.168.0.111/",
        "api_token": "1fcf78e9-4521-4e37-9254-7b34dd3dd936",
        "timezone": "Asia/Kolkata"  # Example timezone, adjust as needed
    },
    "qradar_2": {
        "api_url": "https://another-url/",
        "api_token": "another-api-token",
        "timezone": "Europe/London"  # Example timezone, adjust as needed
    }
}

# Function to get all log sources from a specific QRadar console
def get_log_sources(api_url, api_token):
    url = f"{api_url}api/config/event_sources/log_source_management/log_sources"
    headers = {"Content-Type": "application/json", "SEC": api_token}
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching log sources from {api_url}: {e}")
        return None

# Function to get event collectors from a specific QRadar console
def get_event_collectors(api_url, api_token):
    url = f"{api_url}api/config/event_sources/event_collectors"
    headers = {"Content-Type": "application/json", "SEC": api_token}
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching event collectors from {api_url}: {e}")
        return None

# Function to get log source types from a specific QRadar console
def get_log_source_types(api_url, api_token):
    url = f"{api_url}api/config/event_sources/log_source_management/log_source_types"
    headers = {"Content-Type": "application/json", "SEC": api_token}
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching log source types from {api_url}: {e}")
        return None

# Function to format timestamp with timezone
def format_timestamp(timestamp, timezone_str):
    if timestamp:
        dt_utc = datetime.datetime.fromtimestamp(timestamp / 1000, pytz.utc)
        timezone = pytz.timezone(timezone_str)
        dt_local = dt_utc.astimezone(timezone)
        return dt_local.strftime('%Y-%m-%d %H:%M:%S %Z')
    return 'N/A'

# Function to search log sources by name across all consoles
def search_log_sources_across_consoles(search_name):
    results = []
    for console_name, console_config in qradar_consoles.items():
        api_url = console_config["api_url"]
        api_token = console_config["api_token"]
        timezone_str = console_config.get("timezone", "UTC")

        log_sources = get_log_sources(api_url, api_token)
        if log_sources:
            matching_log_sources = [ls for ls in log_sources if ls.get('enabled') and search_name.lower() in ls.get("name", "").lower()]
            if matching_log_sources:
                event_collectors = get_event_collectors(api_url, api_token)
                log_source_types = get_log_source_types(api_url, api_token)

                for log_source in matching_log_sources:
                    collector_id = log_source.get('target_event_collector_id')
                    collector_name = next((ec.get('name') for ec in event_collectors if ec.get('id') == collector_id), 'Unknown') if event_collectors else 'Unknown'
                    log_source_type_name = get_log_source_type_name(log_source.get('type_id'), log_source_types) if log_source_types else 'Unknown'
                    devices_count = count_devices_for_collector(collector_id, log_sources)

                    last_event_time = format_timestamp(log_source.get('last_event_time'), timezone_str)

                    result = {
                        "Log Source Name": log_source.get('name', 'N/A'),
                        "Log Source Type": log_source_type_name,
                        "Last Event Time": last_event_time,
                        "Target Event Collector": collector_name,
                        "Number of Devices Reporting to Collector": devices_count,
                        "Device Status": 'Enabled' if log_source.get('enabled') else 'Disabled',
                        "Source Console": console_name
                    }
                    results.append(result)
    return results

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

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    if request.method == 'POST':
        search_name = request.form['search_name']
        results = search_log_sources_across_consoles(search_name)
    return render_template('index.html', results=results)

if __name__ == "__main__":
    app.run(debug=True)
