import sys
import os
import glob
import textgrid
import Levenshtein
from tqdm import tqdm
from pprint import pprint

import colorama
colorama.init()


def find_matches_faster2(inword, wordlist, num_alternatives=5, ratios_out=None, force_alternatives=False):

    match_ratios = sorted([(awd, round(Levenshtein.ratio(inword, awd), 3)) for awd in wordlist], reverse=True, key=lambda xx: xx[1])

    # Discard the first match which is the query word itself.
    return match_ratios[1:num_alternatives+1]


def find_matches_faster(inword, wordlist, num_alternatives=5, ratios_out=None, force_alternatives=False):
    '''
    A faster implementation of find_matches() using the Levenshtein C package.
    The returned data type is a list with first item the input word, and
    subsequent items a list of alternative words, if the input word did not occur in the word list (dictionary).
    NB!! Be sure to have wordlist as a set data type for optimal speed -- list data type is slow.
    '''
    
    matches = [inword]

    if inword in wordlist and not force_alternatives:
        return matches
    
    ratios = list()
    for aword in wordlist:
        aratio = Levenshtein.ratio(inword, aword)
        if aratio == 1.0 and not force_alternatives:
            return matches
        ratios.append( (aword, aratio) )
    
    # Sort by element 2 of the tuple, which is the ratio value
    ratios_sorted = sorted(ratios, key=lambda ratio: ratio[1], reverse=True)
    
    # slice out the top scoring num_alternative items from the list
    if ratios_sorted[1][1] != 1.0:
        #matches.extend([alt[0] for alt in ratios_sorted[-1:-num_alternatives-1:-1]])
        matches.extend([alt[0] for alt in ratios_sorted[0:num_alternatives]])
        if ratios_out != None:

#            winratio = ratios_sorted[0][1]
#            for awd,arat in ratios_sorted:
#                if arat == winratio:
#                    ratios_out.append(awd)
#                else:
#                    break

            winratio = ratios_sorted[0][1]
            ratios_out[winratio] = set([])
            for awd,arat in ratios_sorted:
                if arat == winratio:
                    ratios_out[winratio].add(awd)
                else:
                    break
        
    return matches

def find_matches(inword, wordlist, num_alternatives=5):
    '''
    Returns a list of closest matching words.
    The returned data type is a list with first item the input word, and
    subsequent items a list of alternative words, if the input word did not occur in the word list (dictionary).
    '''
    
    matches = difflib.get_close_matches(inword, wordlist, num_alternatives)
    if matches: # check if list is not empty
        matches = [x.strip() for x in matches]
        if matches[0] == inword: # exact match
            matches = [inword]
        elif len(matches) < 5:
            matches.extend([NO_ALTERNATIVE for x in range(0, num_alternatives - len(matches))])
            matches.insert(0, inword)
        else:
            matches.insert(0, inword)
    else:
        matches = [inword]
        matches.extend([NO_ALTERNATIVE for x in range(0, num_alternatives)])
        
    return matches


def get_textgrid_text(atgfn):
    tg = textgrid.TextGrid.fromFile(atgfn)

    return [interval.mark for interval in tg[0]]


def get_textgrid_text_all(atgdir):
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
    return {awty: tokenlist.count(awty) for awty in tqdm(typeslist) if tokenlist.count(awty) > greater_than}


def get_word_lengths(awlist, greater_than=0):
    len_dict = {awd: len(awd) for awd in tqdm(awlist) if len(awd) > greater_than}

    return len_dict


def get_proiritised_list(tokenlist, get_topN=100):

    counts_dict = get_token_counts(tokenlist, list(set(tokenlist)), greater_than=0)
    tokenlist = [awd for awd in tokenlist if awd in counts_dict]
    len_dict = get_word_lengths(list(set(tokenlist)), greater_than=4)
    typeslist = list(len_dict.keys())
    tokenlist = [awd for awd in tokenlist if awd in len_dict]

    combined_list = sorted([(alen, awd, counts_dict[awd], alen + counts_dict[awd]) for awd, alen in len_dict.items()], key=lambda xx: xx[3], reverse=True)
    if get_topN != 0:
        combined_list = combined_list[0:get_topN]

    return combined_list, tokenlist, typeslist

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

def input_parser(input_text, current_state):
    # 
    return answer

PROG_STATES = {
        "current_state": "next_state",
        "landing": ""
        }


if __name__ == "__main__":

    tgdir = "workingdir/textgrids"

    text_all = get_textgrid_text_all(tgdir)
    #text_all.sort()

    tokenlist = split_list(text_all)
    #tokenlist.sort()

    #counts_dict = get_token_counts(tokenlist, list(set(tokenlist)), greater_than=0)
    #tokenlist = [awd for awd in tokenlist if awd in counts_dict]
    #len_list = get_word_lengths(list(set(tokenlist)), greater_than=4)

    #combined_list = sorted([(acnt, awd, counts_dict[awd], acnt + counts_dict[awd]) for acnt, awd in len_list], key=lambda xx: xx[3], reverse=True)
    proiritised_list, tokenlist, typeslist = get_proiritised_list(tokenlist)

    #pprint(text_all)
    #pprint(tokenlist)
    #pprint(counts_dict)
    #pprint(len_list)
    #pprint(proiritised_list)

    for type_count, atup in enumerate(proiritised_list):
        print(atup)
        awd = atup[1]
        #occ_progress_count = 1
        matches = find_matches_faster2(awd, typeslist, num_alternatives=15, force_alternatives=True)
        #pprint(matches)
        for mcnt, amatch in enumerate(matches):
            print("{},{},{}".format(mcnt, amatch[0], amatch[1]))
        print(",")
        response = input("Edit " + awd + " ? [y/n]: ")
        if response == "y":
            atgfn_list = glob.glob(os.path.join(tgdir, "**/*.TextGrid"), recursive=True)
            atgfn_list.sort()

            # First draw up a list of all the occurrences in all the textgrids so that we can
            # traverse them if required
            print("Building the worklist.")
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
            while True:
                # Unpack the items in the worklist
                occ_progress_count, atgfn, interval_count, instance_count = worklist[worklist_idx]

                tg = textgrid.TextGrid.fromFile(atgfn)
                interval =  tg[0][interval_count]
                tg_words = interval.mark.strip().split()
                print("")
                print("Item {} of {}\n".format(occ_progress_count, num_occs))
                print("Found {}{}{} in {} in the sentence:\n".format(colorama.Fore.YELLOW, awd, colorama.Fore.WHITE, os.path.basename(atgfn)))
                print("{}\n".format(set_coloured_word(interval.mark, awd, colorama.Fore.YELLOW, instance=instance_count)))
                pstr = "Change it to:\n"
                for mcnt, amatch in enumerate(matches):
                    pstr += "{:>5}: {:20}\n".format(mcnt, amatch[0])
                pstr += "{:>5}: {:20}\n".format("e", "Or enter a new word that is not in the list above.")
                pstr += "{:>5}: {:20}\n".format("l", "Or mark this item to be addressed at a later time.")
                pstr += "{:>5}: {:20}\n".format("b", "Or go to previous item.")
                pstr += "{:>5}: {:20}\n".format("q", "Or quit.")
                pstr += "{:>5}: {:20}\n".format("", "Pressing Enter without a choice will advance to the next item.")
                print(pstr)
                response = input("Please enter your choice: ")

                if response.isdigit():
                    # A replacement word was selected.
                    try:
                        if int(response) >= 0 and int(response) < len(matches):
                            # A valid number was selected.
                            print("{} was selected.".format(response))
                            # Perform the replacement and log the change.
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
                    matches.append((response, 0.0))
                    worklist_idx += 1
                elif response == "b":
                    # Step back by decrementing the worklist index
                    if worklist_idx > 0:
                        worklist_idx -= 1
                elif response == "l":
                    # Mark for later -- log it and move on.
                    # Move on to the next item in the worklist.
                    worklist_idx += 1
                    continue
                elif response == "q":
                    print("Exiting.")
                    sys.exit(0)
                else:
                    print("\"{}\" is not a valid choice. Please try again.".format(response))
                    continue


        else:
            continue





    sys.exit(0)

