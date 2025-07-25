import os
import re
import pandas as pd
from glob import glob

def parse_log_line(line):
    # Pattern for: %h %l %u %t %m %U %s %b %T
    # Example: 127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] GET /api/v1/resource 200 1234 0.567
    pattern = r'^\S+ \S+ \S+ \[[^\]]+\] (\S+) (\S+) (\d+) (\d+) ([\d\.]+)'
    match = re.match(pattern, line)
    if match:
        method = match.group(1)
        api = match.group(2)
        status = int(match.group(3))
        response_size = int(match.group(4))
        response_time_sec = float(match.group(5))
        response_time = int(response_time_sec * 1000)  # convert to ms
        return api, response_time, response_size
    return None

def parse_logs_from_folder(folder_path):
    data = []
    for file_path in glob(os.path.join(folder_path, '*.log')):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                parsed = parse_log_line(line)
                if parsed:
                    api, response_time, response_size = parsed
                    data.append({'api': api, 'response_time': response_time, 'response_size': response_size})
    return pd.DataFrame(data)

if __name__ == "__main__":
    import sys
    folder = sys.argv[1] if len(sys.argv) > 1 else '.'
    df = parse_logs_from_folder(folder)
    print(df.head()) 