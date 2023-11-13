import os
import shutil
import time
import subprocess
import pydicom
from tqdm import tqdm
from colorama import init, Fore

# Initialize colorama
init()


def count_files(directory):
    file_count = 0

    for root, dirs, files in os.walk(directory):
        file_count += len(files)

    return file_count


def copy_cd_contents(patient_name, source_folder, destination_folder, progress_bar):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # Get the total number of files
    total_files = count_files(source_folder)
    processed_files = 0

    # Iterate over the contents of the source folder
    for item in os.listdir(source_folder):
        source_item = os.path.join(source_folder, item)
        destination_item = os.path.join(destination_folder, item)

        if os.path.isdir(source_item):
            # Recursively copy subdirectories
            copy_cd_contents(patient_name, source_item, destination_item, progress_bar)
        else:
            try:
                # Read the file with PyDICOM
                ds = pydicom.dcmread(source_item, force=False)

                # Check if patient name is present and update it
                ds.PatientName = patient_name
                ds.save_as(destination_item)

                processed_files += 1

            except pydicom.errors.InvalidDicomError:
                pass

            progress_bar.update(1)  # Update the progress bar

    return processed_files, total_files


def ask_user_input(defaults=None):
    if defaults is None:
        defaults = {}

    study = input(f"Enter study name [{Fore.YELLOW}{defaults.get('study', '')}{Fore.RESET}]: ").strip() or defaults.get('study', '')
    site = input(f"Enter site name [{Fore.YELLOW}{defaults.get('site', '')}{Fore.RESET}]: ").strip() or defaults.get('site', '')
    subject = input(f"Enter subject name [{Fore.YELLOW}{defaults.get('subject', '')}{Fore.RESET}]: ").strip() or defaults.get('subject', '')
    timepoint = input(f"Enter timepoint [{Fore.YELLOW}{defaults.get('timepoint', '')}{Fore.RESET}]: ").strip() or defaults.get('timepoint', '')

    return study, site, subject, timepoint


def save_user_input_values(values):
    with open('user_input.txt', 'w') as f:
        for key, value in values.items():
            f.write(f"{key}={value}\n")


def load_user_input_values():
    values = {}
    if os.path.isfile('user_input.txt'):
        with open('user_input.txt', 'r') as f:
            for line in f:
                key, value = line.strip().split('=')
                values[key] = value
    return values


def find_cd_mount_point():
    # Get the list of mounted volumes
    mounted_volumes = os.listdir("/Volumes")

    # Filter the list to find CD volumes
    cd_volumes = []
    for volume in mounted_volumes:
        if volume != "Macintosh HD":
            cd_volumes.append(volume)
    return cd_volumes


def main():
    # Specify the destination folder
    destination_folder = os.path.expanduser("~/Downloads")

    while True:
        print(f"{Fore.RED}Checking...{Fore.RED}")

        # Find mounted CD volumes
        cd_volumes = find_cd_mount_point()

        # Check if any CD volumes are detected
        if cd_volumes:
            print(f"{Fore.GREEN}CD loaded!{Fore.RESET}")
            print("Available CD Volumes:")

            # Load previous user input values
            user_input_values = load_user_input_values()

            for i, volume in enumerate(cd_volumes):
                # Ask for user input
                study, site, subject, timepoint = ask_user_input(user_input_values)

                # Store user input values for future use
                user_input_values = {
                    'study': study,
                    'site': site,
                    'subject': subject,
                    'timepoint': timepoint
                }
                save_user_input_values(user_input_values)

                source = os.path.join("/Volumes", volume)
                source_file_count = count_files(source)

                # Create a new folder in the destination path using the entered information
                pt_name = f"{study}-{site}_{subject}-{timepoint}"
                new_folder_path = os.path.join(destination_folder,study, pt_name)
                os.makedirs(new_folder_path, exist_ok=True)

                # Initialize the tqdm progress bar
                progress_bar = tqdm(total=source_file_count, unit='file(s)', desc='Copying files')

                # Copy contents of the CD to the new folder and get progress
                processed_files, total_files = copy_cd_contents(
                    pt_name,
                    source,
                    new_folder_path,
                    progress_bar,
                )

                # Close the progress bar
                progress_bar.close()

                subprocess.run(
                    [
                        "diskutil",
                        "eject",
                        os.path.join("/Volumes", volume),
                    ]
                )

        # Sleep for a while before checking again
        time.sleep(1)


if __name__ == "__main__":
    main()
