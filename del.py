import os

# Define the directory path
directory = 'Videos'

# List all files in the directory
files = os.listdir(directory)

print(" ".join(files))
