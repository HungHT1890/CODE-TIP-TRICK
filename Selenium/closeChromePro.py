import os
import time
import pandas as pd
import psutil
import time
import pandas as pd
import psutil
p = psutil.Process(os.getpid())
p.nice(psutil.HIGH_PRIORITY_CLASS)


def extract_process_data(proc):
    # Initialize the data for this process
    data = {
        'pid': proc.info['pid'],
        'name': proc.info['name'],
        'create_time': proc.info['create_time']
    }
    # Extract the renderer client ID and user data directory
    for arg in proc.info['cmdline']:
        if arg.startswith('--renderer-client-id='):
            data['renderer-client-id'] = arg.split('=')[1]
        elif arg.startswith('--user-data-dir='):
            data['user-data-dir'] = arg.split('=')[1]
    return data


def add_dir_group_count(df):
    # Count the number of processes per user-data-dir
    dir_group_count = df.groupby('user-data-dir').size()
    # Add the count to the DataFrame
    df = df.merge(dir_group_count.rename('dir_group_count'), left_on='user-data-dir', right_index=True)
    return df


def kill_processes(pids):
    # Iterate over the process IDs and kill each process
    for pid in pids:
        try:
            proc = psutil.Process(pid)
            proc.kill()
            # # print(f"Killed process {pid}")
        except psutil.NoSuchProcess:
            pass
            # print(f"Process {pid} does not exist")
        except Exception as e:
            pass
            # print(f"Error killing process {pid}: {e}")


def kill_chrome_garbage_processes():
    try:
        # print(f'{datetime.now()} Start killing Chrome garbage processes')
        # Initialize an empty list to store process data
        process_data = []
        # Iterate over all running processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            # Filter out non-Chrome processes
            if 'chrome' in proc.info['name']:
                # Extract necessary data from each Chrome process
                data = extract_process_data(proc)
                # Add the data to the list
                process_data.append(data)
        if len(process_data) == 0:
            # print('No Chrome processes found')
            return
        # Convert the list of process data into a DataFrame
        df = pd.DataFrame(process_data)
        # Add a column to the DataFrame that counts the number of processes per user-data-dir
        df = add_dir_group_count(df)
        df['seconds_exist'] = time.time() - df['create_time']
        # print(df['seconds_exist'].mean())
        # Fill missing renderer-client-id values with the first non-null value in the same user-data-dir group
        df['renderer-client-id'] = df['renderer-client-id'].fillna(
            df.groupby('user-data-dir')['renderer-client-id'].transform('first'))
        # Get a list of process IDs that need to be killed
        df = df.sort_values(['dir_group_count', 'user-data-dir']).reset_index(drop=True).copy()
        # print(df[['pid', 'dir_group_count', 'user-data-dir', 'renderer-client-id']].shape)
        # & (df['renderer-client-id'].apply(str).isin(['7', '30', '31', '32',])))

        pids_to_kill = df.loc[
            (df['dir_group_count'].apply(str).isin(['1', '2', '3', '4', '5', '1.0', '2.0', '3.0', '4.0', '5.0']))
            , 'pid'].tolist()
        # print(f"PIDS to kill all {len(pids_to_kill)}", pids_to_kill)
        pids_to_kill = df.loc[
            (df['dir_group_count'].apply(str).isin(['1', '2', '3', '4', '5', '1.0', '2.0', '3.0', '4.0', '5.0']))
            & (df['seconds_exist'] > 10)
            , 'pid'].tolist()
        # print(f"PIDS to kill only old {len(pids_to_kill)}", pids_to_kill)
        # Kill the processes
        kill_processes(pids_to_kill)
    except Exception as e:
        # print(e)
        pass

if __name__ == '__main__':
    kill_chrome_garbage_processes()