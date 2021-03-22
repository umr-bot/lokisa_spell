"""
This program applies the changes that are logged when using the Lokisa Spell program. Output files are generated into a pre-created folder named changed_log_files. The generated textgrids with changed text is named as the entire path to the file with forward slashes replaced by double underscores as follows:
    original file name: 'some/file/path.TextGrid'
    generated name: 'some__file__path.TextGrid'
"""

__author__ = "Umr Barends"
__affiliation__ = "Stellenbosch University"
__date__ = "2021-02-23"

from tabCompleter import *

def parse_change_log(log_dir):
    """Find all lines that contain changes to be made in log file and return these lines as a list of strings.

    Parameters
    ----------
    log_dir : str
        The path of the directory to the log file to be parsed

    Returns
    -------

    list
        a list of strings that contain the changes to be made to the 
        original transcript/textgrid file.
    """
    try:
        with open(log_dir) as f:
            log = [line for line in f]
        substring = ":Change"
        lines = []
        cnt = 0

        for line in log:
            if line.find(substring) != -1:
                lines.append(line)
                cnt +=1

        print(str(cnt) + " changes to be made found!\n")
        return lines

    except FileNotFoundError as error:
        print(error)
        print("Check if log file directory is typed correctly and if the file exists")
        return ''

def decode_log_string(log_string):
    """Decodes the changes that must be made from the log file

    Parameters
    ----------

    log_string : str
        string that is to be decoded from the log file

    Returns
    -------

    tuple
        a tuple containing tokens required to change the textgrid file
    """

    print(log_string)
    log_string_tokens = log_string.split(" ")
    search_word = log_string_tokens[2]
    textgrid_dir = log_string_tokens[5]
    interval = log_string_tokens[7]
    correction = log_string_tokens[11].rstrip()
    return search_word, textgrid_dir, interval, correction

def apply_changes(log_dir):
    """Applies the changes that were logged

    Parameters
    ----------

    log_dir : str
        The path of the directory to the log file to be parsed

    altered_textgrid_fn : str
        The file name of the textgrid that has been altered

    Returns:
    --------

    TextGrid
        a textgrid file that has had changes made on it
    """
    
    log_strings = parse_change_log(log_dir)
    if log_strings == []: return -1
    altered_textgrid_fn = 'altered_'+log_dir
    print(altered_textgrid_fn) 
    
    if not os.path.exists('changed_log_files'):
        os.makedirs('changed_log_files')
    
    for log_string in log_strings:
        search_word, textgrid_dir, interval, correction = decode_log_string(log_string)
        with open(textgrid_dir, encoding='utf-16') as f:
            textgrid = [line for line in f]
        interval_string = "intervals [" + interval + "]"

        for i in range(0,len(textgrid)):
            if interval_string in textgrid[i]: 
                print(correction)
                print(textgrid[i+3])
                textgrid[i+3] = textgrid[i+3].replace(search_word,correction).rstrip()
                print(textgrid[i+3])
        fn = 'changed_log_files/' + textgrid_dir.replace('/','__')
        with open(fn,"w+") as f:
            for line in textgrid: f.write(line)

    return 0

def main():

    tab = tabCompleter()
    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(tab.pathCompleter)

    file_name = input("Input logfile directory : ")

    print()
    if apply_changes(file_name) != -1: print("Changes successfull!")
    else : print('Changes not made')
if __name__ == "__main__":
    main()
