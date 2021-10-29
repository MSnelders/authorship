import re
import numpy as np
import sys
import argparse
import string

parser = argparse.ArgumentParser(description="""This script will parse two google sheets into one .tex file suitable for large N author papers.
                                                Useage:
                                                python authors.py author_sheet.tsv affiliation_sheet.tsv > outfile.tex""")
parser.add_argument('auth_tsv')
parser.add_argument('affil_tsv')
parser.add_argument('--discard',
                    type=int,
                    default=3,
                    help='Number of lines to discard from the top of the authors spreadsheet (default: %(default)s).')
parser.add_argument('--discard-affil',
                    type=int,
                    default=1,
                    help='Number of lines to discard from the top of the affiliations spreadsheet (default: %(default)s).')
parser.add_argument('--apj',
                    type=str,
                    default='True',
                    help='if --apj True, will create the author list in ApJ(L) format (default: %(default)s).')
parser.add_argument('--nature',
                    type=str,
                    default='False',
                    help='if --nature True, will create the author list in Nature format (default: %(default)s).')
parser.add_argument('--sort_lastname',
                    type=str,
                    default='False',
                    help='if --sort_lastname True, it will sort the authors on their lastname. Else, it will keep the order of the google sheet (default: %(default)s).')
parser.add_argument('--initials',
                    type=str,
                    default='True',
                    help='if --initials True will replace non-surnames with initials. I.e. Mark P Snelders -> M.~P.~Snelders (default: %(default)s).')


#
# Here we assume the spreadsheet has columns:
#
# | Lastname  |  First names  |  x  |  x  |  ORCID  |  Affiliations  |  Acks  | ...
#
# And we assume that the affiliations spreadsheet has two columns:
#
# | Affiliations | Affiliation_Acronyms |
#
parser.add_argument('--lastname_index',
                    type=int,
                    default=0,
                    help='Index of author last name in spreadsheet (default: %(default)s).')
parser.add_argument('--firstname_index',
                    type=int,
                    default=1,
                    help='Index of author non-last names in spreadsheet (default: %(default)s).')
parser.add_argument('--orcid_index',
                    type=int,
                    default=4,
                    help='Index of author ORCID in spreadsheet (default: %(default)s).')
parser.add_argument('--affil_index',
                    type=int,
                    default=5,
                    help='Index of author affiliation acronyms in spreadsheet (default: %(default)s).')
parser.add_argument('--ack_index',
                    type=int,
                    default=6,
                    help='Index of author acknowledgements in spreadsheet (default: %(default)s).')

opt = parser.parse_args()

def debug(*args):
    print(*args, file=sys.stderr)

def name_to_initials(name):
    namesplit = name.split() # 'Mark P Snelders' -> ['Mark', 'P', 'Snelders']
    newname = [x[0] for x in namesplit] # ['Mark', 'P', 'Snelders'] -> ['M', 'P', 'S']
    newname[-1] = namesplit[-1] # ['M', 'P', 'S'] -> ['M', 'P', 'Snelders']
    newname = ".~".join(newname) # ['M', 'P', 'Snelders'] -> M.~P.~Snelders
    if not (newname[0] in string.ascii_letters):
        debug("WARNING: Possible problem found with the name: {}. Current outname: {}".format(name, newname))
    return newname

def fix_umlaut(name):
    chars_to_fix = [('Ä', '\\"{A}'), ('ä', '\\"{a}'), ('Ë', '\\"{E}'),\
                    ('ë', '\\"{e}'), ('Ï', '\\"{I}'), ('ï', '\\"{i}'),\
                    ('Ö', '\\"{O}'), ('ö', '\\"{o}'), ('Ü', '\\"{u}'),\
                    ('ü', '\\"{u}'), ('Ÿ', '\\"{Y}'), ('ÿ', '\\"{y}')]
    for c in chars_to_fix:
        name = name.replace(c[0], c[1])
    return name

def check_input(opt):
    if opt.apj == opt.nature == True:
        debug("Either --apj or --nature is True, not both.")
        exit()

def main(opt):
    check_input(opt)
    # Export Google spreadsheet as TSV...
    f  = open(opt.auth_tsv) #'authors-cat.tsv'
    f2 = open(opt.affil_tsv) #'affils-cat.tsv'

    # A regex for finding initials in names, like "Rob, Bob G."
    initial_rex = re.compile(r'(\w[.]) ?(\w)')

    # Parse authors spreadsheet
    # discard header lines (column headers, etc)
    for i in range(opt.discard):
        line = f.readline()
        debug('Discarding:', line)

    authors = []
    acks = []
    lastnames = []
    for line in f.readlines():
        words = line.replace('\n','').replace('  ', ' ').split('\t')

        lastname  = words[opt.lastname_index ]
        firstname = words[opt.firstname_index]
        orcid     = words[opt.orcid_index]
        affils    = words[opt.affil_index]
        ack       = words[opt.ack_index]

        # Split affiliations by semicolons OR commas
        # (because people can't follow instructions...)
        affils = [a.strip() for a in affils.split(';')]
        aa = []
        for a in affils:
            aa.extend([a.strip() for a in a.split(',')])
        affils = aa
        # drop any empty strings
        affils = [a for a in affils if len(a)]

        lastname  = lastname.strip()
        firstname = firstname.strip()
        name = firstname + ' ' + lastname

        # The author list can be sorted by lastname
        lastnames.append(lastname)

        # Mark: I don't think this actually works
        # Search for and stick "~" characters in initials, to produce
        # better Latex spacing.
        while True:
            m = initial_rex.search(name)
            if not m:
                break
            #debug('Match:', name, '->', m)
            #debug(m[0], '/', m[1], '/', m[2])
            name = name[:m.start()] + m[1]+'~'+m[2] + name[m.end():]

        # fix umlauts
        name = fix_umlaut(name)

        if len(ack):
            acks.append(ack)

        if opt.initials == 'True':
            name = name_to_initials(name)

        authors.append((name, orcid, affils))

    # Parse affiliation acronym expansion spreadsheet
    f = f2
    for i in range(opt.discard_affil):
        line = f.readline()
        debug('Discarding:', line)
    affilmap = {}
    for line in f.readlines():
        words = line.replace('\n','').replace('  ', ' ').split('\t')
        full,acro = words
        affilmap[acro] = full



    if opt.sort_lastname == 'True':
        # Sort by last name
        I = np.argsort(lastnames)
        authors = [authors[i] for i in I]
        lastnames = [lastnames[i] for i in I]
    debug('Last names:', lastnames)

    # ApJ format
    if opt.apj == 'True':
        for auth,orcid,affil in authors:
            orctxt = ''
            if len(orcid):
                orctxt = '[%s]' % orcid
            print('\\author%s{%s}' % (orctxt, auth))
            for aff in affil:
                print('  \\affiliation{%s}' % affilmap.get(aff, aff))

    # Nature format
    if opt.nature == 'True':
        txt = []
        uaffils = []
        txt.append('\\author{')
        for iauth,(auth,orcid,affil) in enumerate(authors):
            sups = []
            for aff in affil:
                if aff in uaffils:
                    i = uaffils.index(aff)
                else:
                    i = len(uaffils)
                    uaffils.append(aff)
                sups.append(i+1)
            sep = ',' if iauth < len(authors)-1 else ''

            affiltxt = ''
            if len(sups):
                affiltxt = '$^{%s}$' % (','.join(['%i'%i for i in sups]))
            txt.append('%s%s%s \\allowbreak' % (auth, affiltxt, sep))

        txt.append('}')
        txt.append('\\newcommand{\\affils}{')
        txt.append('\\begin{affiliations}')
        for aff in uaffils:
            #txt.append('\\item{%s}' % aff)
            debug('Looking up', aff)
            txt.append('\\item{%s}' % affilmap.get(aff, aff))
        txt.append('\\end{affiliations}')
        txt.append('}')
        print('\n'.join(txt))

    acks = list(set(acks))
    acks.sort()
    print('% Unique acks:')
    print(r'\newcommand{\allacks}{')
    for ack in acks:
        #debug('% ', ack)
        print(ack.replace('&', r'\&'))
        print('%')
    print(r'}')

if __name__ == '__main__':
    opt = parser.parse_args()
    main(opt)
