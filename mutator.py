# Mutator Program
import os
import shutil
import fileinput
import random
import sys
import subprocess
import multiprocessing
import time
import datetime

# Code taken from https://stackoverflow.com/a/19308592
# Gets a list of files given a directory, crawls subfolders too


def get_filepaths(directory):

    # List which will store all of the full filepaths.
    file_paths = []

    # Blacklist of files we should ignore
    files_blacklist = [
        "abc", "__init__", "conftest", "release", "setup", "coreerrors"]

    # Blacklist of directories to skip
    directories_blacklist = [
        "tests", "__pycache__", "assumptions", "benchmarks", "external"
        "utilities", "deprecated", "printing"]

    # Walk the tree.
    for root, directories, files in os.walk(directory):

        for filename in files:

            # We only want files to be mutated and tested in the list
            if not filename.startswith(tuple(files_blacklist)) and \
                    root not in tuple(directories_blacklist) and \
                    filename.endswith(".py"):

                # Join the two strings in order to form the full filepath.
                filepath = os.path.join(root, filename)

                # Add it to the list.
                file_paths.append(filepath)

    # Self-explanatory.
    return file_paths

# Runs the test suite relative to the mutant
# as a child worker


def run_suite(dirname):

    # Change directory
    os.chdir(dirname)

    (path, mutant_name) = os.path.split(dirname)

    passed_flag = True

    # Execute program
    print("Executing Test Suite: %s" % mutant_name)

    # Call the testing process and capture output to host_output_file
    data_stream = subprocess.Popen(
        "python setup.py test",
        bufsize=1,
        stdout=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

    # As each line is read from the process
    # if we find DO *NOT* COMMIT or [FAIL], we fail
    for line in data_stream.stdout:

        if b"[FAIL]" in line:
            passed_flag = False
            return (passed_flag, mutant_name, line)

        if b"DO *NOT* COMMIT" in line:

            # Didn't pass, return false
            passed_flag = False
            return (passed_flag, mutant_name, line)

    # Passed, return true
    return (passed_flag, mutant_name, "")


# Mutates file given file name and dictionary of mutation operators
def mutate(mutant_file, mutant_dict, output_log):

    # This is set to True so we know we still need to mutate
    mutation_flag = True

    # This is a flag that is toggled as the file is read line by line
    multiline_comment = False

    # This flag is toggled once we successfully mutate something
    mutant_flag = False

    # Count for lines in file
    linecount = 1

    # Read the file line by line
    with fileinput.FileInput(mutant_file, inplace=True) as file:

        # Line by line
        for line in file:

            if line.count("\"\"\"") == 0 and multiline_comment:
                # Middle of multiline comment

                # Just print to file and move on
                sys.stdout.write(line)
                continue

            if line.count("\"\"\"") == 1 and multiline_comment:
                # End of multiline comment
                multiline_comment = False

                # Print to file and move on
                sys.stdout.write(line)
                continue

            if line.count("\"\"\"") == 1 and multiline_comment is False:
                # Beginning of multiline comment
                multiline_comment = True

                # Print to file and move on
                sys.stdout.write(line)
                continue

            if "#" in line or \
               "\"" in line or \
               "raise" in line or \
               "assert" in line or \
               "import" in line:
                # We want to skip mutation on:
                # Single comment lines, quotes, and raise/asserts
                sys.stdout.write(line)
                continue

            if line.count("\"\"\"") == 2:
                # We want to skip mutation on """comment lines"""
                sys.stdout.write(line)
                continue

            # If we still want to mutate the file
            if mutation_flag and not multiline_comment:

                # Look for a smybol to replace (only 1 per line)
                # Dicts are unordered, so no need to randomize
                for key, value in mutant_dict.items():

                    if mutation_flag is False:
                        break

                    # If we found a match and we still want to mutate
                    if line.find(key) != -1 and mutation_flag is True:

                        # Replace it and move to the next line
                        # Set the flag to false, so we only swap one symbol
                        output_log.write("In: %s " % (str(mutant_file)))
                        output_log.write(
                            "(Line %s)\n %s" % (str(linecount), line))
                        output_log.write(
                            "Found %s, replacing with %s\n" % (key, value))

                        line = line.replace(key, value, 1)

                        sys.stderr.write("New line: %s\n" % (line))

                        # We don't need to look to mutate anymore
                        mutation_flag = False

                        # We sucessfully mutated
                        mutant_flag = True

                        break

            # inplace=True in FileInput redirects stdout to the file
            # print() adds new lines, so use this to print normally
            sys.stdout.write(line)
            linecount += 1

    # Return flag for while loop
    return mutant_flag

# Main function
if __name__ == '__main__':

    # Start time
    start_time = time.monotonic()

    mutant_number = 10

    if len(sys.argv) == 2:
        mutant_number = int(sys.argv[1])

    # Build dict of symbols to replace
    # E.g > to <, / to *
    # Dicts are naturally unordered, so it provides built in random choices
    mutant_dict = {' > ': ' < ', ' * ': ' / ', ' != ': ' == ', ' - ': ' + ',
                   ' < ': ' > ', ' / ': ' * ', ' == ': ' != ', ' + ': ' - ',
                   ' >= ': ' <= ', '-=': '+=', ' <= ': ' >= ', '+=': '-=',
                   ' % ': ' * ', ' ^ ': ' & ', ' and ': ' or ',
                   ' * ': ' % ', ' & ': ' ^ ', ' or ': ' and '}

    # List of mutant directory names (mutant0, mutant1, etc)
    mutants = []

    output_log = open("executionlog.txt", "w")

    # Generate mutants
    for num in range(mutant_number):

        dirname = "mutations" + str(num)
        mutants.append(os.path.join(os.getcwd(), dirname))

        output_log.write("\nMutant %s\n" % str(num))

        # If mutations folder exists, delete and recopy
        if os.path.isdir(dirname):
            output_log.write("Previous mutations found, deleting...\n")
            shutil.rmtree("mutations" + str(num))
            output_log.write("Deleted!  Copying new files...\n")

        # Copy files so we can run tests on individual mutants using setup.py

        # Copy sympy directory as mutation#\sympy
        shutil.copytree("sympy", dirname + "\sympy")

        # Copy setup.py to mutation#\setup.py
        shutil.copyfile("setup.py", dirname + "\setup.py")
        output_log.write("Files copied!\n")

        # Get a list of .py files from the newly created mutations folder
        files_to_mutate = get_filepaths(dirname)

        # We haven't sucessfully created a mutant yet
        mutation_result = False

        while mutation_result is False:

            # Get random file from list of files to mutate
            mutation_target = random.choice(files_to_mutate)

            # Mutate file, returns True if successful, False if not
            mutation_result = mutate(mutation_target, mutant_dict, output_log)

        # Let us know which file we mutated
        output_log.write("Mutation finished!\n")
        output_log.write("Mutated: %s\n" % str(mutation_target))

    output_log.write("\n\nRunning Mutant Test Suites...\n\n")

    output_log.close()

    mutation_fails = 0
    failed_mutant_dirs = []

    # Use multiple processes to increase speed of testing
    p = multiprocessing.Pool()

    # Async execution of different mutation suites
    for result, name, line in p.imap(run_suite, mutants):

        output_log = open("executionlog.txt", "a")

        # Returns TRUE/FALSE = Mutant ALIVE/DEAD, mutant name, and line
        if result:

            # We found an alive mutant
            output_log.write("%s PASSED!\n" % str(name))
            print("%s PASSED!" % str(name))
        else:

            # Delete failures
            output_log.write("%s failed (%s)\n" % (str(name), str(line)))
            print("%s failed (%s)" % (str(name), str(line)))

            failed_mutant_dirs.append(str(name))
            mutation_fails += 1

    # Calculate mutation score
    mutation_score = round(((mutation_fails / mutant_number) * 100), 2)
    print("Mutation Score: %s%%" % str(mutation_score))
    output_log.write("Mutation Score: %s%%" % str(mutation_score))

    # Delete failed mutant dirs
    for mutant_dir in failed_mutant_dirs:
        shutil.rmtree(mutant_dir)

    # End time
    end_time = time.monotonic()

    # Calculate how long it took
    time_taken = datetime.timedelta(seconds=end_time - start_time)

    # Print/log information
    print("Time taken for %s canidates: %s" %
          (str(mutant_number), str(time_taken)))
    output_log.write("Time taken for %s canidates: %s" % (
        str(mutant_number), str(time_taken)))

    # Close and be done
    output_log.close()
