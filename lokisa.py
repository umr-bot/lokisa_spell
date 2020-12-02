"""
Lokisa Spell

This simple progam tries to identify spellings in TextGrid transcriptions
that are closely match and may thus be either spelling mistakes or spelling
variations of a word.
"""

__author__ = "Ewald van der Westhuizen"
__affiliation__ = "Stellenbosch University"
__date__ = "2020-09-29"

import sys
import os
import glob
import textgrid
import Levenshtein
import logging
import datetime
import argparse
from tqdm import tqdm
from pprint import pprint

import colorama
colorama.init()


def log_and_print(message):
    print(message)
    logging.info(message.strip())


def parse_command_line_arguments():
    """Check the command line arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mandatory_wordlist_fn",
        help="File name of a text file that contains a list of words that are mandatory to handle.",
    )
    parser.add_argument(
        "--logdir",
        default="log",
        help="Directory where to store the log files. Default is log/",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Activate a debug mode.",
    )

    #if len(sys.argv) == 1:
    #    parser.print_help()
    #    sys.exit(1)

    return parser.parse_args()


def find_matches_faster(inword, wordlist, num_alternatives=None, ratio_threshold=0.0):
    """
    Use Levenshtein to find match word with closely matching spellings.
    Returns a list with tuples (word_label, Levenshtein_ratio)
    """

    match_ratios = sorted([(awd, round(Levenshtein.ratio(inword, awd), 3)) for awd in wordlist], reverse=True, key=lambda xx: xx[1])
    # Discard the first match which is the query word itself.
    if match_ratios[0][1] == 1.0:
        match_ratios = match_ratios[1:]

    if ratio_threshold > 0.0:
        match_ratios = [(awd, levrat) for awd, levrat in match_ratios if levrat >= ratio_threshold]

    # Get the set of ratios
    ratios_list = sorted(list(set([arat for awd, arat in match_ratios])), reverse=True)

    # Pick from the highest ratios until we have the required number of alternatives
    match_ratios_new = []

    if num_alternatives:
        if len(ratios_list) <= num_alternatives:
            match_ratios_new = match_ratios
        else:
            ratio_cmp = ratios_list[num_alternatives-1]
            for amatch in match_ratios:
                if amatch[1] >= ratio_cmp:
                    match_ratios_new.append(amatch)
                else:
                    break
    else:
        match_ratios_new = match_ratios

    return match_ratios_new

def get_textgrid_text(atgfn):
    tg = textgrid.TextGrid.fromFile(atgfn)

    return [interval.mark for interval in tg[0]]


def get_textgrid_text_all(atgdir):
    """
    Find all the TextGrid files in the given directory and read in all the
    annotations. Return the annotations as a list of text string.
    """
    atgfn_list = glob.glob(os.path.join(atgdir, "**/*.TextGrid"), recursive=True)
    atgfn_list.sort()

    text_list = []
    for atgfn in tqdm(atgfn_list):
        text_list.extend(get_textgrid_text(atgfn))

    return text_list

def split_list(
        inlist,
        remove_fra=True,
        remove_ara=True,
        remove_eng=True,
        remove_misses=True,
        remove_junk=True,
        remove_fillers=True
        ):
    """
    Split each list item (assumed to be a line of text) into
    words and flatten to not have line or sentence boundaries.
    Also performs some cleanup for the given 'remove_' options.
    Returns a list of all the word tokens.
    """
    removes = []
    if remove_fra:
        removes += '_fra'
    if remove_ara:
        removes += '_ara'
    if remove_eng:
        removes += '_eng'
    removes = tuple(removes)
    tokenlist = []

    for aline in tqdm(inlist):
        awrdlist = aline.strip().split()
        if removes:
            awrdlist = [awd for awd in awrdlist if not awd.endswith(removes)]
        if remove_misses:
            awrdlist = [awd for awd in awrdlist if '[' not in awd or ']' not in awd]
        if remove_junk:
            awrdlist = [awd for awd in awrdlist if 'JUNK' != awd]
        if remove_fillers:
            awrdlist = [awd for awd in awrdlist if not awd.startswith("<fil>")]
        tokenlist.extend(awrdlist)

    return tokenlist

def get_token_counts(tokenlist, typeslist, greater_than=0):
    """
    Calculate the occurrence counts of each word type given the full list of word tokens.
    The counts are return as a dictionary where the key is the word type and the value is the count.
    """
    return {awty: tokenlist.count(awty) for awty in tqdm(typeslist) if tokenlist.count(awty) > greater_than}


def get_word_lengths(awlist, greater_than=0):
    """
    Calculate the length of each word in the given word list and return the result
    as a dictionary, where the key is the word type and the value is the length.
    """
    len_dict = {awd: len(awd) for awd in tqdm(awlist) if len(awd) > greater_than}

    return len_dict


def get_prioritised_list(tokenlist, get_topN=100, mandatory_wordlist=None, num_alternatives=None, ratio_threshold=0.0):
    """
    Build a prioritised list of word types that should be considered for
    checking. The top N (default N=100) word types are returned.
    The returned tuples are:
    (word_length, word_label, frequency_count, priority_score)
    """

    log_and_print("Calculating occurrence counts.")
    counts_dict = get_token_counts(tokenlist, list(set(tokenlist)), greater_than=0)
    tokenlist = [awd for awd in tokenlist if awd in counts_dict]
    log_and_print("Calculating word lengths.")
    len_dict = get_word_lengths(list(set(tokenlist)), greater_than=4)
    typeslist = list(len_dict.keys())
    tokenlist = [awd for awd in tokenlist if awd in len_dict]

    combined_list = sorted([(alen, awd, counts_dict[awd], alen + counts_dict[awd]) for awd, alen in len_dict.items()], key=lambda xx: xx[3], reverse=True)

    # Move/add mandatory words to the top of the list.
    if mandatory_wordlist:
        for amanwd in reversed(mandatory_wordlist):
            #print("Mandatory word:", amanwd)
            if amanwd in typeslist:
                # If a mandatory word is already in the combined list, move it to the top
                for aidx, atuple in enumerate(combined_list):
                    alen, awd, count_val, priority_val = atuple
                    if awd == amanwd:
                        combined_list.insert(0, combined_list.pop(aidx))
                        break
            else:
                # If a mandatory word is not in the corpus, what do we do?
                print("The mandatory word,", amanwd,", does not occur in the corpus. Ignoring it.")

    # Refine the list by grouping together the closest Levenshtein matches to form "word sets" for checking and editing.
    log_and_print("Refining the prioritised word list.")
    combined_list2 = []
    added_set = set([])
    for alen, awd, count_val, priority_val in tqdm(combined_list):
        if awd not in added_set:
            added_set.add(awd)
            wordset = []
            matches = find_matches_faster(awd, typeslist, num_alternatives=num_alternatives, ratio_threshold=ratio_threshold)
            for amatch in matches:
                if amatch[0] not in added_set:
                    wordset.append((len_dict[amatch[0]], amatch[0], counts_dict[amatch[0]], len_dict[amatch[0]] + counts_dict[amatch[0]]))
                    added_set.add(amatch[0])
            # Add the word from the outer foor loop too.
            wordset.append((alen, awd, count_val, priority_val))
            combined_list2.append(wordset)

    if len(added_set) != len(typeslist):
        print("len(added_set) != len(typeslist)")
        print(len(added_set), "!=", len(typeslist))

    #if get_topN != 0:
    #    combined_list = combined_list[0:get_topN]

    return combined_list2, tokenlist, typeslist


def set_coloured_word(astr, awrd, colorama_colour, instance=0):
    icount = 0
    newstr = []
    for bwrd in astr.strip().split():
        if awrd == bwrd:
            if icount == instance:
                newstr.append(colorama_colour + bwrd + colorama.Fore.WHITE)
            else:
                newstr.append(bwrd)
            icount += 1
        else:
            newstr.append(bwrd)

    return " ".join(newstr)


#def print_main_prompt(prioritised_list, start_idx=0, end_idx=10):
def print_main_prompt(wordset_list, wordset_idx, num_word_sets):
    """
    Print the main menu and wait for a response.
    Return the value of the response.
    """

    print("\n=========================================================================================================")
    print("=========================================================================================================\n")
    print("Word set", wordset_idx, "of", num_word_sets,"\n")
    astr = "Which word do you wish to work on?\n"
    for tcount, atup in enumerate(wordset_list):
        #if tcount >= start_idx and tcount < end_idx:
        astr += "{:>4}: {:20} [Occurence count:{:5};  pscore:{:5}]\n".format(tcount, atup[1], atup[2], atup[3])
    astr += "{:>4}: {}\n".format("n", "Next word set.")
    astr += "{:>4}: {}\n".format("b", "Previous word set.")
    astr += "{:>4}: {}\n".format("q", "To quit the program.")
    print(astr)
    response = input("Enter your choice: ")
    return response


def handle_digits(invalue, limhi, limlo=0, action_fc=None):
    """
    Parse a numerical response by the user and call an
    action function if it is provided.
    Returns True if not parsing error occurred.
    Returns False if a parsing error occurred.
    """
    retcode = False
    try:
        if int(invalue) >= limlo and int(invalue) < limhi:
            retcode = True
            # A valid number was selected.
            print("You chose {}.".format(invalue))
            # Perform the replacement and log the change.
            if action_fc is not None:
                action_fc(invalue)
        else:
            # Not a valid number. Retry.
            print("\"{}\" is not a valid choice. Please try again.".format(invalue))
            retcode = False
    except ValueError:
        print("\"{}\" is not a valid choice. Please try again.".format(invalue))
        retcode = False

    return retcode


def handle_wordtype(awd, tgdir, typeslist, num_alternatives=None, ratio_threshold=0.0):
    """
    """

    matches = find_matches_faster(awd, typeslist, num_alternatives=num_alternatives, ratio_threshold=ratio_threshold)

    atgfn_list = glob.glob(os.path.join(tgdir, "**/*.TextGrid"), recursive=True)
    atgfn_list.sort()

    # First draw up a list of all the occurrences in all the textgrids so that we can
    # traverse them if required
    log_and_print("Building the worklist.")
    worklist = []
    occ_cnt = 0
    for atgfn in tqdm(atgfn_list):
        tg = textgrid.TextGrid.fromFile(atgfn)
        #for interval in tg[0]:
        for icnt in range(len(tg[0])):
            interval =  tg[0][icnt]
            tg_words = interval.mark.strip().split()
            for icount in range(tg_words.count(awd)):
                worklist.append((occ_cnt, atgfn, icnt, icount))
                occ_cnt += 1
    #pprint(worklist)
    num_occs = len(worklist)

    #for occ_progress_count, atgfn, interval_count, instance_count in worklist:
    worklist_idx = 0
    while worklist_idx < len(worklist):
        # Unpack the items in the worklist
        occ_progress_count, atgfn, interval_count, instance_count = worklist[worklist_idx]

        tg = textgrid.TextGrid.fromFile(atgfn)
        interval =  tg[0][interval_count]
        tg_words = interval.mark.strip().split()
        print("\n=========================================================================================================")
        print("=========================================================================================================\n")
        print("Occurence number {} of {}\n".format(occ_progress_count+1, num_occs))
        print("Found {}{}{} in {} in the sentence:\n".format(colorama.Fore.YELLOW, awd, colorama.Fore.WHITE, os.path.basename(atgfn)))
        print("{}\n".format(set_coloured_word(interval.mark, awd, colorama.Fore.YELLOW, instance=instance_count)))
        pstr = "Change it to:\n"
        for mcnt, amatch in enumerate(matches):
            pstr += "{:>5}: {:20} [match ratio: {}]\n".format(mcnt, amatch[0], amatch[1])
        pstr += "{:>5}: {:20}\n".format("e", "Or enter a new word that is not in the list above.")
        pstr += "{:>5}: {:20}\n".format("l", "Or enter a note or comment for this item.")
        pstr += "{:>5}: {:20}\n".format("b", "Or go to previous item.")
        pstr += "{:>5}: {:20}\n".format("q", "Or quit.")
        pstr += "{:>5}: {:20}\n".format("", "Pressing Enter without a choice will advance to the next occurrence.")
        print(pstr)
        response = input("Please enter your choice: ")

        if response.isdigit():
            # A replacement word was selected.
            try:
                if int(response) >= 0 and int(response) < len(matches):
                    # A valid number was selected.
                    print("{} was selected.".format(response))
                    # Log the change.
                    log_and_print("Change {} in file {} interval {} instance {} to {}".format(
                        awd,
                        worklist[worklist_idx][1],
                        worklist[worklist_idx][2]+1,
                        worklist[worklist_idx][3]+1,
                        matches[int(response)][0]))

                else:
                    # Not a valid number. Retry.
                    print("\"{}\" is not a valid choice. Please try again.".format(response))
                    continue
            except ValueError:
                print("\"{}\" is not a valid choice. Please try again.".format(response))
                continue

            # Move on to the next item in the worklist.
            worklist_idx += 1
            continue

        elif response == "":
            # Move on to the next item in the worklist without any edits.
            worklist_idx += 1
        elif response == "e":
            # Enter a new word as the correct replacement and add it to the matches list.
            response = input("Enter the new word and press Enter: ")
            log_and_print("Change {} in file {} interval {} instance {} to {}".format(
                awd,
                worklist[worklist_idx][1],
                worklist[worklist_idx][2]+1,
                worklist[worklist_idx][3]+1,
                response))
            matches.append((response, 0.0))
            worklist_idx += 1
        elif response == "b":
            # Step back by decrementing the worklist index
            if worklist_idx > 0:
                worklist_idx -= 1
        elif response == "l":
            # Enter a note for this item, log it and move on.
            response = input("Enter a note to save for this item and press Enter: ")
            log_and_print("A note has been saved for {} in file {} interval {} instance {}:\n\n \"{}\"\n".format(
                awd,
                worklist[worklist_idx][1],
                worklist[worklist_idx][2]+1,
                worklist[worklist_idx][3]+1,
                response))
            input("Press Enter to continue.")
            # Move on to the next item in the worklist.
            worklist_idx += 1
            continue
        elif response == "q":
            log_and_print("Quiting for \"{}\"".format(awd))
            break
        else:
            print("\"{}\" is not a valid choice. Please try again.".format(response))
            continue



def main():

    prioritised_list_ratio_threshold = 0.7
    prioritised_list_max_alternatives = 2
    ratio_threshold = 0.7
    max_alternatives = 4
    mandatory_wordlist = None

    args = parse_command_line_arguments()

    # Log everything that happens during the session in a log file.
    logdir = args.logdir
    os.makedirs(logdir, exist_ok=True)
    dtnow = datetime.datetime.now()
    datestr = dtnow.strftime("%y%m%d_%H%M%S")

    logging.basicConfig(**{
        "filename": os.path.join(logdir, "logfile_{}.txt".format(datestr)),
        "level": logging.INFO,
        "format": "%(levelname)s:%(name)s:%(asctime)s:%(message)s"
        })
    logging.info("Starting Lokisa Spell.")


    tgdir = "workingdir/textgrids"

    log_and_print("\n\nFinding and parsing all TextGrid files in {}".format(tgdir))
    text_all = get_textgrid_text_all(tgdir)
    #text_all.sort()

    log_and_print("Extracting all word tokens.")
    tokenlist = split_list(text_all)
    #tokenlist.sort()

    if args.mandatory_wordlist_fn:
        # Load word from the mandatory word list file
        with open(args.mandatory_wordlist_fn, "r") as fid:
            mandatory_wordlist = [awd.strip() for awd in fid]


    #counts_dict = get_token_counts(tokenlist, list(set(tokenlist)), greater_than=0)
    #tokenlist = [awd for awd in tokenlist if awd in counts_dict]
    #len_list = get_word_lengths(list(set(tokenlist)), greater_than=4)

    #combined_list = sorted([(acnt, awd, counts_dict[awd], acnt + counts_dict[awd]) for acnt, awd in len_list], key=lambda xx: xx[3], reverse=True)
    log_and_print("Prioritising word types.")
    prioritised_list, tokenlist, typeslist = get_prioritised_list(tokenlist, mandatory_wordlist=mandatory_wordlist, num_alternatives=prioritised_list_max_alternatives, ratio_threshold=prioritised_list_ratio_threshold)


    #pprint(text_all)
    #pprint(tokenlist)
    #pprint(counts_dict)
    #pprint(len_list)
    #pprint(prioritised_list)

    mainmenu_start_idx = 0
    mainmenu_list_length = 10
    wordset_idx = 0
    while True:

        wordset_list = prioritised_list[wordset_idx]
        
        #response = print_main_prompt(prioritised_list[wordset_idx], start_idx=mainmenu_start_idx, end_idx=mainmenu_start_idx+mainmenu_list_length)
        response = print_main_prompt(wordset_list, wordset_idx+1, len(prioritised_list))

        if response.isdigit():
            #retcode = handle_digits(response, len(prioritised_list))
            retcode = handle_digits(response, len(wordset_list))
            if retcode is False:
                input("Press Enter to continue.")
                continue
            else:
                #awd = prioritised_list[int(response)][1]
                awd = wordset_list[int(response)][1]
                log_and_print("Let's work on \"{}\"".format(awd))
                input("Press Enter to continue.")
                handle_wordtype(awd, tgdir,  typeslist, num_alternatives=max_alternatives, ratio_threshold=ratio_threshold)
                log_and_print("Going back to the main menu.")
                input("Press Enter to continue.")

        elif response == "q":
            break

        elif response == "n":
            if wordset_idx + 1 < len(prioritised_list):
                wordset_idx += 1

        elif response == "b":
            if wordset_idx > 0:
                wordset_idx -= 1

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("")

