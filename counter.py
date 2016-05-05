# Mutator Program
import os
import fileinput

mutant_dict = {' > ': 0, ' * ': 0, ' != ': 0, ' - ': 0,
               ' < ': 0, ' / ': 0, ' == ': 0, ' + ': 0,
               ' >= ': 0, '-=': 0, ' <= ': 0, '+=': 0,
               ' % ': 0, ' ^ ': 0, ' and ': 0,
               ' * ': 0, ' & ': 0, ' or ': 0}


# Code taken from https://stackoverflow.com/a/19308592
# Gets a list of files given a directory, crawls subfolders too


def get_filepaths(directory):

    # List which will store all of the full filepaths.
    file_paths = []

    # Blacklist of files we should ignore
    files_blacklist = [
        "abc", "__init__", "conftest", "release", "setup", "coreerrors"]

    # Walk the tree.
    for root, directories, files in os.walk(directory):

        for filename in files:

            # We only want files to be mutated and tested in the list
            if not filename.startswith(tuple(files_blacklist)) and \
                    "tests" not in root and \
                    "__pycache__" not in root and \
                    "assumptions" not in root and \
                    "benchmarks" not in root and \
                    "external" not in root and \
                    "utilities" not in root and\
                    "deprecated" not in root and \
                    "printing" not in root and \
                    filename.endswith(".py"):

                # Join the two strings in order to form the full filepath.
                filepath = os.path.join(root, filename)

                # Add it to the list.
                file_paths.append(filepath)

    # Self-explanatory.
    return file_paths


# Mutates file given file name and dictionary of mutation operators
def mutate(mutant_file):

    # This is set to True so we know we still need to mutate
    mutation_flag = True

    # This is a flag that is toggled as the file is read line by line
    multiline_comment = False

    # Read the file line by line
    with open(mutant_file, "r") as file:

        lines = file.readlines()

        # Line by line
        for line in lines:

            if line.count("\"\"\"") == 0 and multiline_comment:
                # Middle of multiline comment
                continue

            if line.count("\"\"\"") == 1 and multiline_comment:
                # End of multiline comment
                multiline_comment = False
                continue

            if line.count("\"\"\"") == 1 and multiline_comment is False:
                # Beginning of multiline comment
                multiline_comment = True
                continue

            if "#" in line or \
               "\"" in line or \
               "raise" in line or \
               "assert" in line or \
               "import" in line:
                continue

            if line.count("\"\"\"") == 2:
                continue

            # If we still want to mutate the file
            if mutation_flag and not multiline_comment:

                # Look for a smybol to replace (only 1 per line)
                # Dicts are unordered, so no need to randomize
                for key in mutant_dict:

                    # If we found a match and we still want to mutate
                    if line.find(key) != -1:

                        mutant_dict[key] += 1

# Get a list of .py files from the newly created mutations folder
files_to_mutate = get_filepaths("sympy")

# We haven't sucessfully created a mutant yet
mutation_result = False

for file in files_to_mutate:
    mutate(file)

total = 0

for key, val in mutant_dict.items():
    total += val

for key, value in mutant_dict.items():
    print("%s: (%s%%) of the symbols" % (key, round((value / total) * 100, 2)))
