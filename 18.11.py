import paramiko
import time
import json

# Function to read data from a JSON file
def read_credentials_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data.get('username'), data.get('password')

# Function to check if the usaer wants to record again
def ask_for_re_recording():
    return input("Do you want to record again? (y/n): ").lower() == 'y'

# Read data from the JSON file
data_file_path = "C:/Users/katar/Desktop/deneme/credentials.json"
username, password = read_credentials_from_json(data_file_path)

# Set the SSH connection details
raspberry_pi_hostname = "raspberrypi"
port = 22
recordings_folder = "/home/pi/kayitlar"
recordings_folder2 = "/home/pi"
local_folder = "C:/Users/katar/Desktop/deneme/"
microphone_name = "dmic_sv"  

# Initialize the SSH client
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            
try:
    # Connect to the Raspberry Pi
    ssh.connect(raspberry_pi_hostname, port, username, password)

    # Dmic device setup 
    local_path1 = "C:/Users/katar/Desktop/deneme/dmic.txt"
    remote_path1 = f"{recordings_folder2}/.asoundrc"
    sftp = ssh.open_sftp()
    sftp.put(local_path1,remote_path1)
    sftp.close()

    while True:
        # Prompt the user to enter the file name for recording
        file_name = input("Enter the file name for recording (e.g., recording1.wav): ")
        remote_path = f"{recordings_folder}/{file_name}"

    
        
        # Save the recording setup to a file on Raspberry Pi
        setup_command = f"echo 'DEVICE={microphone_name}\nDURATION=10\nSAMPLE_RATE=44100\nCHANNELS=2\nOUTPUT_FILE={remote_path}\nFORMAT=S32_LE' > {recordings_folder}/recording_setup.txt"
        stdin, stdout, stderr = ssh.exec_command(setup_command)
        print("Recording setup saved on Raspberry Pi.")

        # Start recording in the background
        start_command = f"bash -c 'source {recordings_folder}/recording_setup.txt && nohup arecord -D $DEVICE -r $SAMPLE_RATE -c $CHANNELS -f $FORMAT -t wav -V mono $OUTPUT_FILE &'"
        stdin, stdout, stderr = ssh.exec_command(start_command)
        print("Recording started on Raspberry Pi. Press ENTER to stop recording.")

        # Wait for the user to press ENTER to stop recording
        input("Press ENTER when you want to stop recording.")

        # Stop recording (send SIGTERM)
        stop_command = f"kill -INT $(ps aux | grep '[a]record -D {microphone_name}' | awk '{{print $2}}')"
        ssh.exec_command(stop_command)
        print("Recording stopped on Raspberry Pi.")

        # Wait for a moment to ensure the recording process has stopped
        time.sleep(2)

        # Get any error output from the recording process
        error_output = stderr.read().decode('utf-8')
        if error_output:
            print(f"Error during recording: {error_output}")

        # Prompt the user to confirm downloading the file
        confirm_download = input("Do you want to download the recorded file? (y/n): ").lower()
        if confirm_download == 'y':
            # SFTP the recorded file to the local machine
            local_path = f"{local_folder}{file_name}"
            sftp = ssh.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            print(f"File downloaded to: {local_path}")

            # Prompt the user to confirm deleting the recorded file from Raspberry Pi
            confirm_delete = input("Do you want to delete the recorded file on Raspberry Pi? (y/n): ").lower()
            if confirm_delete == 'y':
                delete_command = f"rm {remote_path}"
                ssh.exec_command(delete_command)
                print("Recorded file deleted on Raspberry Pi.")
            else:
                print("Recorded file not deleted on Raspberry Pi.")
        else:
            print("File not downloaded.")

        # Ask if the user wants to record again
        if not ask_for_re_recording():
            print("Exiting the program. Goodbye!")
            break
        else:
            print("Recording again...")

finally :
    # Close the SSH connection
    ssh.close()