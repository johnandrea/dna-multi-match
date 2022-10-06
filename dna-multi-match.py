#!/usr/bin/python3

"""
Find the intersection of DNA test matches from multiple people.

This code is released under the MIT License: https://opensource.org/licenses/MIT
Copyright (c) 2022 John A. Andrea
v0.9.2

No support provided.
"""

import sys
import argparse
import importlib.util
import re
import os

MATCH_COLOR = 'orange'
BASE_COLOR = 'lightblue'


def load_my_module( module_name, relative_path ):
    """
    Load a module in my own single .py file. Requires Python 3.6+
    Give the name of the module, not the file name.
    Give the path to the module relative to the calling program.
    Requires:
        import importlib.util
        import os
    Use like this:
        readgedcom = load_my_module( 'readgedcom', '../libs' )
        data = readgedcom.read_file( input-file )
    """
    assert isinstance( module_name, str ), 'Non-string passed as module name'
    assert isinstance( relative_path, str ), 'Non-string passed as relative path'

    file_path = os.path.dirname( os.path.realpath( __file__ ) )
    file_path += os.path.sep + relative_path
    file_path += os.path.sep + module_name + '.py'

    assert os.path.isfile( file_path ), 'Module file not found at ' + str(file_path)

    module_spec = importlib.util.spec_from_file_location( module_name, file_path )
    my_module = importlib.util.module_from_spec( module_spec )
    module_spec.loader.exec_module( my_module )

    return my_module


def looks_like_int( s ):
    return re.match( r'\d\d*$', s )


def get_program_options():
    results = dict()

    orientations = [ 'tb', 'lr', 'bt', 'rl' ]

    results['infile'] = None
    results['testers'] = None
    results['max-results'] = 14
    results['min-testers'] = 3
    results['smallest-match'] = 866 #average 1st cousin
    results['orientation'] = 'lr'
    results['id-item'] = 'xref'
    results['show-each'] = False
    results['reverse'] = False
    results['libpath'] = '.'

    arg_help = 'Display intersection of potential matches from multiple testers.'
    parser = argparse.ArgumentParser( description=arg_help )

    arg_help = 'At least one match must have a DNA value bigger than this value. Default: ' + str(results['smallest-match'])
    parser.add_argument( '--smallest-match', default=results['smallest-match'], type=int, help=arg_help )

    arg_help = 'Orientation of the output dot file tb=top-bottom, lt=left-right, etc. Default:' + results['orientation']
    parser.add_argument( '--orientation', default=results['orientation'], type=str, help=arg_help )

    arg_help = 'Minimum number of needed testers. Default ' + str(results['min-testers'])
    parser.add_argument( '--min-testers', default=results['min-testers'], type=int, help=arg_help )

    arg_help = 'Maximum number of matches in results. Default ' + str(results['max-results'])
    parser.add_argument( '--max-results', default=results['max-results'], type=int, help=arg_help )

    arg_help = 'How to find the person in the input. Default is the gedcom id "xref".'
    arg_help += ' Othewise choose "type.exid", "type.refnum", etc.'
    parser.add_argument( '--id-item', default=results['id-item'], type=str, help=arg_help )

    arg_help = 'Show matches of each tester to stderr. Might result in a lot of output.'
    parser.add_argument( '--show-each', default=results['show-each'], action='store_true', help=arg_help )

    # in dot files, change direction of the arrows
    arg_help = 'For dot file output, reverse the order of the link arrows.'
    parser.add_argument( '--reverse-arrows', default=results['reverse'], action='store_true', help=arg_help )

    # maybe this should be changed to have a type which better matched a directory
    arg_help = 'Location of the gedcom library. Default is current directory.'
    parser.add_argument( '--libpath', default=results['libpath'], type=str, help=arg_help )

    arg_help = 'Set of id,dna-value for each of the testers. Need at least ' + str(results['min-testers'])
    parser.add_argument( '--testers', type=str, nargs='+', help=arg_help )

    parser.add_argument('infile', type=argparse.FileType('r') )

    args = parser.parse_args()

    results['testers'] = args.testers
    results['id-item'] = args.id_item.lower()
    results['max-results'] = args.max_results
    results['min-testers'] = args.min_testers
    results['smallest-match'] = args.smallest_match
    results['show-each'] = args.show_each
    results['infile'] = args.infile.name
    results['reverse'] = args.reverse_arrows
    results['libpath'] = args.libpath

    # easy to get this one wrong, just drop back to default
    if args.orientation.lower() in orientations:
       results['orientation'] = args.orientation.lower()

    return results


def are_options_ok( program_options ):
    # Error messages will be printed in this routine.

    result = True

    # the set of testers must be id comma dna-match
    n = 0
    for tester in program_options['testers']:
        n += 1
        err_prefix = 'Tester #' + str(n)
        show_test = '"' + tester + '"'

        if ',' in tester:
           parts = tester.split(',')
           if len( parts ) == 2:
              if looks_like_int( parts[1] ):
                 dna = int( parts[1] )
                 if not 1 <= dna <= 4000:
                    print( err_prefix, 'has out of range dna value"', show_test, file=sys.stderr )
                    result = False
              else:
                 print( err_prefix, 'does not have positive integer for dna value:', show_test, file=sys.stderr )
                 result = False
           else:
              print( err_prefix, 'is not id,dna', show_test, file=sys.stderr )
              result = False
        else:
           print( err_prefix, 'is not id,dna:', show_test, file=sys.stderr )
           result = False

    expecting = program_options['min-testers']
    if n < expecting:
       print( 'Expected', expecting, 'pairs of id,dna for the testers. Found', n, file=sys.stderr )
       result = False

    for item in ['max-results', 'min-testers']:
        x = program_options[item]
        if x <= 0:
           print( 'Option', item, 'must be greater than zero, not', x, file=sys.stderr )
           result = False

    for item in ['smallest-match']:
        x = program_options[item]
        if x <= 1:
           print( 'Option', item, 'must be greater than 1, not', x, file=sys.stderr )
           result = False

    return result


def define_dna_ranges():
   # values via DNA Painter Shared cM Project
   # https://dnapainter.com/tools/sharedcmv
   #
   # Note the use of non-gender specific labels
   # "auncle" = "aunt or uncle"
   # "nibling" = "niece or nephew"

   results = dict()
   results['1C'] = {'min':396, 'max':1397, 'ave':866}
   results['1C1R'] = {'min':102, 'max':980, 'ave':433}
   results['1C2R'] = {'min':33, 'max':471, 'ave':221}
   results['1C3R'] = {'min':25, 'max':238, 'ave':117}
   results['2C'] = {'min':41, 'max':592, 'ave':229}
   results['2C1R'] = {'min':14, 'max':353, 'ave':122}
   results['2C2R'] = {'min':0, 'max':244, 'ave':71}
   results['2C3R'] = {'min':0, 'max':154, 'ave':51}
   results['3C'] = {'min':0, 'max':234, 'ave':73}
   results['3C1R'] = {'min':0, 'max':192, 'ave':48}
   results['3C2R'] = {'min':0, 'max':166, 'ave':36}
   results['3C3R'] = {'min':0, 'max':98, 'ave':27}
   results['4C'] = {'min':0, 'max':139, 'ave':35}
   results['4C1R'] = {'min':0, 'max':126, 'ave':28}
   results['4C2R'] = {'min':0, 'max':93, 'ave':22}
   results['4C3R'] = {'min':0, 'max':60, 'ave':19}
   results['5C'] = {'min':0, 'max':117, 'ave':25}
   results['5C1R'] = {'min':0, 'max':80, 'ave':21}
   results['5C2R'] = {'min':0, 'max':65, 'ave':18}
   results['5C3R'] = {'min':0, 'max':30, 'ave':13}
   results['6C'] = {'min':0, 'max':71, 'ave':18}
   results['6C1R'] = {'min':0, 'max':56, 'ave':15}
   results['6C2R'] = {'min':0, 'max':45, 'ave':13}
   results['7C'] = {'min':0, 'max':57, 'ave':14}
   results['7C1R'] = {'min':0, 'max':50, 'ave':12}
   results['auncle'] = {'min':1201, 'max':2282, 'ave':1741}
   results['child'] = {'min':2376, 'max':3720, 'ave':3487}
   results['g-grandauncle'] = {'min':186, 'max':713, 'ave':420}
   results['g-grandchild'] = {'min':485, 'max':1486, 'ave':887}
   results['g-grandnibling'] = {'min':186, 'max':713, 'ave':420}
   results['g-grandparent'] = {'min':485, 'max':1486, 'ave':887}
   #results['g-grandparents'] = {'min':485, 'max':1486, 'ave':887}
   results['grandauncle'] = {'min':330, 'max':1467, 'ave':850}
   results['grandchild'] = {'min':984, 'max':2462, 'ave':1754}
   results['grandnibling'] = {'min':330, 'max':1467, 'ave':850}
   results['grandparent'] = {'min':984, 'max':2462, 'ave':1754}
   #results['grandparents'] = {'min':984, 'max':2462, 'ave':1754}
   results['half-1C'] = {'min':156, 'max':979, 'ave':449}
   results['half-1C1R'] = {'min':62, 'max':469, 'ave':224}
   results['half-1C2R'] = {'min':16, 'max':269, 'ave':125}
   results['half-1C3R'] = {'min':0, 'max':120, 'ave':60}
   results['half-2C'] = {'min':10, 'max':325, 'ave':120}
   results['half-2C1R'] = {'min':0, 'max':190, 'ave':66}
   results['half-2C2R'] = {'min':0, 'max':144, 'ave':48}
   results['half-3C'] = {'min':0, 'max':168, 'ave':48}
   results['half-3C1R'] = {'min':0, 'max':139, 'ave':37}
   results['half-3C2R'] = {'min':0, 'max':78, 'ave':27}
   results['half-auncle'] = {'min':492, 'max':1315, 'ave':871}
   results['half-g-grandauncle'] = {'min':103, 'max':284, 'ave':208}
   results['half-gg-nibling'] = {'min':103, 'max':284, 'ave':208}
   results['half-grandauncle'] = {'min':184, 'max':668, 'ave':431}
   results['half-grandnibling'] = {'min':184, 'max':668, 'ave':431}
   results['half-nibling'] = {'min':492, 'max':1315, 'ave':871}
   results['half-sibling'] = {'min':1160, 'max':2436, 'ave':1759}
   results['nibling'] = {'min':1201, 'max':2282, 'ave':1740}
   results['parent'] = {'min':2376, 'max':3720, 'ave':3485}
   #results['parents'] = {'min':2376, 'max':3720, 'ave':3485}
   results['sibling'] = {'min':1613, 'max':3488, 'ave':2613}

   return results


def find_relation_label( relation_data ):
    # return a string of the relationship of "them" to "me"
    # as "grandparent", "1C", "auncle", etc
    # given the generation distance to the nearest common ancestor family
    #
    # Note the use of non-gender specific labels
    # "auncle" = "aunt or uncle"
    # "nibling" = "niece or nephew"
    #
    # Note that the labels used here must be the same as in the dna-range setup.

    me = relation_data['gen-me']
    them = relation_data['gen-them']

    result = 'N/A'

    if them == 0:
       # direct line
       if me == 0:
          result = 'self'
       elif me == 1:
          result = 'parent'
       elif me == 2:
          result = 'grandparent'
       else:
          result = 'g' * (me - 2) + '-grandparent'

    elif me == 0:
         # direct line
         if them == 0:
            result = 'self'
         elif them == 1:
            result = 'child'
         elif them == 2:
            result = 'grandchild'
         else:
            result = 'g' * (them - 2) + '-grandchild'

    elif me == 1:
         if them == 1:
            result = 'sibling'  #or half-sibling by checking parents family
         elif them == 2:
            result = 'nibling'
         elif them == 3:
            result = 'grandnibling'
         else:
            result = 'g' * (them - 3) + '-grandnibling'

    elif me == them:
         if me == 0:
            result = 'self'
         elif me == 1:
            result = 'sibling' #or half-sibling
         else:
            result = str(me - 1) + 'C'

    elif them == 1:
         if me == 2:
            result = 'auncle'
         elif me == 3:
            result = 'grandauncle'
         else:
            result = 'g' * (me - 3) + '-grandauncle'

    elif me == 2:
        result = '1C' + str(them - 2) + 'R'

    elif me > 2:
         y = abs( them - me )
         if them < me:
            # older generation
            result = str(them - 1) + 'C' + str(y) + 'R'
         else:
            # younger generation
            result = str(me - 1) + 'C' + str(y) + 'R'

    return result


def get_name( individual ):
    """ Return the name for the individual in the passed data section. """
    name = individual['name'][0]['value']
    # the standard unknown code is not good for svg output
    if '?' in name and '[' in name and ']' in name:
       name = 'unknown'
    return name.replace( '/', '' ).replace('"','&quot;').replace("'","&rsquo;")


def get_names( get_indis, family ):
    """ Return names of both people in the family, by id """
    results = dict()
    for partner in ['husb','wife']:
        if partner in family:
           partner_id = family[partner][0]
           results[partner_id] = get_name( get_indis[partner_id] )
    return results


def make_label( indi_data, people_info ):
    label = 'DNA matches between'
    for indi in people_info:
        label += '\\n' + get_name( indi_data[indi] ) + ' @ ' + str(people_info[indi]) + ' cM'
    return label


def make_dot_id( xref ):
    return xref.lower().replace('@','').replace('i','').replace('f','').replace('.','')

def make_fam_dot_id( xref ):
    return 'f' + make_dot_id( str(xref) )

def make_indi_dot_id( xref ):
    return 'i' + make_dot_id( str(xref) )


def start_dot( label, orientation ):
    """ Start of the DOT output file """
    print( 'digraph family {' )
    print( 'node [shape=record];' )
    print( 'rankdir=' + orientation + ';' )
    print( 'labelloc="t";' )
    print( 'label="' + label + '";' )


def end_dot():
    """ End of the DOT output file """
    print( '}' )


def dot_labels( ged_indis, ged_fams, base_people, people_of_interest, people_in_fams ):
    def output_label( dot_id, s, extra ):
        print( dot_id, '[label=' + s.replace("'",'.') + extra + '];' )

    match_style = ',style=filled,color=' + MATCH_COLOR
    base_style = ',style=filled,color=' + BASE_COLOR

    for indi in people_of_interest:
        # a family person will be added later
        if indi not in people_in_fams:
           name = get_name( ged_indis[indi] ).strip()
           with_color = match_style
           if indi in base_people:
              with_color = base_style
           output_label( make_indi_dot_id(indi), '"' + name + '"', with_color )

    # find the families to draw
    fams_in_use = dict()

    # the parents of the people are always drawn
    for indi in people_of_interest:
        fam = people_of_interest[indi]
        if fam not in fams_in_use:
           fams_in_use[fam] = []

    # other families along the paths,
    # tracking whick ones have a partner which also links to parents
    for indi in people_in_fams:
        for from_to in people_in_fams[indi]:
            for fam_type in ['from','to']:
                fam = from_to[fam_type]
                if fam not in fams_in_use:
                   fams_in_use[fam] = []
                fams_in_use[fam].append( indi )

    for fam in fams_in_use:
        names = get_names( ged_indis, ged_fams[fam] )
        extra_info = ''
        text = ''
        for indi in names:
            if indi in people_of_interest:
               extra_info = match_style
            if indi in base_people:
               extra_info = base_style
            if text:
               # second parent
               text += '|<p>|'
            text += '<' + make_indi_dot_id(indi) + '>' + names[indi].strip()
        output_label( make_fam_dot_id(fam), '"' + text + '"', extra_info )


def dot_connect( reverse, people_of_interest, people_in_fams ):
    def make_dup_check( one, two ):
        return str(one) +':'+ str(two)

    # this is a hack
    # why are doubles produced
    already_used = []

    for indi in people_of_interest:
        dup_test = make_dup_check( indi, people_of_interest[indi] )
        if dup_test in already_used:
           continue
        already_used.append( dup_test )
        indi_dot = make_indi_dot_id(indi)
        fam_dot = make_fam_dot_id(people_of_interest[indi] +':p' )
        if reverse:
           print( fam_dot, '->', indi_dot )
        else:
           print( indi_dot, '->', fam_dot )

    for indi in people_in_fams:
        for from_to in people_in_fams[indi]:
            dup_test = make_dup_check( from_to['from'], from_to['to'] )
            already_used.append( dup_test )
            from_fam = make_fam_dot_id( from_to['from'] )
            to_fam = make_fam_dot_id( from_to['to'] )
            indi_dot = make_indi_dot_id(indi)
            if reverse:
               print( to_fam + ':p', '->', from_fam +':' + indi_dot )
            else:
               print( from_fam +':' + indi_dot, '->', to_fam + ':p' )


def get_ancestor_families( indi, ged_indis, ged_fams ):
    # Return the list of ancestor families for the given person as
    # { fam1:g, fam2:g, fam3:g, ... }
    # where g is the number of generations from the person to the ancestor family.
    #
    # Algorithm note:
    # each person will be touched multiple times, but the lists are not large.

    results = dict()

    key = 'famc'
    if key in ged_indis[indi]:
       fam = ged_indis[indi][key][0]

       results[fam] = 1

       for parent in ['husb','wife']:
           if parent in ged_fams[fam]:
              parent_id = ged_fams[fam][parent][0]

              parent_ancestors = get_ancestor_families( parent_id, ged_indis, ged_fams )

              for ancestor_fam in parent_ancestors:
                  results[ancestor_fam] = parent_ancestors[ancestor_fam] + 1

    return results


def find_nearest_common_ancestors( person, person_families, everyones_ancestor_fams, ged_fams ):
    results = dict()

    # Find the people who are blood relatives
    # If is an ancestor or shared ancestors
    # Save the closest ancestor family and the distance to that family

    # Return a dict with each blood relative
    # [blood-relative-id] = { 'closest': closest-family-id,
    #                         'gen-me': generations-from-person-to-closest-family,
    #                         'gen-them': generations-from-relative-to-closest-family }
    #
    # By which "me" is the "person" being handled.
    # If the blood relative is a parent gen-me -> 1, gen-them -> 0
    # i.e. generations from them to themselves is zero.
    # If the blood relative is a grandparent gen-me -> 2, gen-them -> 0

    persons_ancestor_fams = everyones_ancestor_fams[person]

    # first get the people who are direct blood ancestors
    for fam in persons_ancestor_fams:
        for partner in ['husb','wife']:
            if partner in ged_fams[fam]:
               ancestor_id = ged_fams[fam][partner][0]
               d = persons_ancestor_fams[fam]
               results[ancestor_id] = { 'closest':fam, 'gen-me':d, 'gen-them':0 }

    # find descendants
    for them in everyones_ancestor_fams:
        if person == them:
           continue  # skip self
        if them in results:
           continue  # skip already added
        for ancestor_fam in everyones_ancestor_fams[them]:
            if ancestor_fam in person_families:
               d = everyones_ancestor_fams[them][ancestor_fam]
               results[them] = { 'closest':ancestor_fam, 'gen-me':0, 'gen-them':d }
               continue # found

    # then each person who isn't an ancestor or descendant
    for them in everyones_ancestor_fams:
        if person == them:
           continue  # skip self
        if them in results:
           continue  # skip already added
        them_ancestor_fams = everyones_ancestor_fams[them]
        closest = None
        gen_to_them = None
        gen_to_me = 1000 # a big number of generations to start
        for ancestor_fam in persons_ancestor_fams:
            if ancestor_fam in them_ancestor_fams:
               # compare gen distance to person
               new_gen = persons_ancestor_fams[ancestor_fam]
               if new_gen < gen_to_me:
                  gen_to_them = them_ancestor_fams[ancestor_fam]
                  gen_to_me = new_gen
                  closest = ancestor_fam
               break
        if closest is not None:
           results[them] = {'closest':closest, 'gen-me':gen_to_me, 'gen-them':gen_to_them }

    return results


def find_ids_of_testers( tag, testers, individuals ):
    # testers with id problems will not to be added to the list.
    # The calling routine ought to check that all are present in order to continue.
    # Errors will be printed in this routine.
    results = dict()
    n = 0
    for test in testers:
        n += 1
        found_id = None
        id_ok = True
        err_prefix = 'Tester #' + str(n)
        show_test = '"' + test + '"'

        parts = test.split(',')

        if tag == 'xref':
           # maybe the user has given the full id "@Ix@" or just the number
           # so reduce it to just the number
           wanted = parts[0].replace('@','').replace('I','').replace('i','')
           if looks_like_int( wanted ):
              wanted = int( wanted )
              # search using the xref key because that's more future-proof than the main id key
              for indi in individuals:
                  if individuals[indi]['xref'] == wanted:
                     found_id = indi
                     break

           else:
              id_ok = False
              print( err_prefix, 'id isn\'t an xref number:', show_test, file=sys.stderr )

        elif tag.startswith( 'type.' ):
           subtag = tag.replace( 'type.', '' )
           for indi in individuals:
               if 'even' in individuals[indi]:
                  for event in individuals[indi]['even']:
                      if 'type' in event and event['type'] == subtag:
                         if event['value'] == parts[0]:
                            found_id = indi
                            break

        else:
           # its a top level tag of some sort, maybe even uuid
           # Hopefully not "name" or "sex" or something else not useful
           for indi in individuals:
               if tag in individuals[indi]:
                  if individuals[indi][tag] == parts[0]:
                     found_id = indi
                     break

        if found_id is None:
           if id_ok:
              print( err_prefix, 'not located in the GEDCOM:', show_test, file=sys.stderr )
        else:
           results[found_id] = int( parts[1] )

    return results


def person_info( indi ):
    return get_name( data[i_key][indi] ) + ' (xref ' + str(data[i_key][indi]['xref']) + ')'

options = get_program_options()

if not are_options_ok( options ):
   sys.exit(1)

if not os.path.isdir( options['libpath'] ):
   print( 'Path to readgedcom is not a directory', file=sys.stderr )
   sys.exit( 1 )

readgedcom = load_my_module( 'readgedcom', options['libpath'] )

i_key = readgedcom.PARSED_INDI
f_key = readgedcom.PARSED_FAM

data = readgedcom.read_file( options['infile'] )

dna_ranges = define_dna_ranges()

testers = find_ids_of_testers( options['id-item'], options['testers'], data[i_key] )
if len( testers ) != len( options['testers'] ):
   # error messages have already been printed
   sys.exit(1)

# There is a limit to the usefullness of low quality matches
# but this is a guess at this limit.
# Maybe a large number of low quality matches is ok.

biggest_dna = 0
for indi in testers:
    biggest_dna = max( biggest_dna, testers[indi] )
if biggest_dna < options['smallest-match']:
   print( 'At least one match must be greater than', options['smallest-match'], file=sys.stderr )
   sys.exit(1)

# everyone gets a list of all their ancestors

ancestor_fams = dict()
for indi in data[i_key]:
    ancestor_fams[indi] = get_ancestor_families( indi, data[i_key], data[f_key] )

# everyone gets a list of all their blood relativs

blood_related = dict()
for indi in testers:
    # first determine, which families have this person as a parent
    as_parent = []
    if 'fams' in data[i_key][indi]:
       as_parent = data[i_key][indi]['fams']

    blood_related[indi] = find_nearest_common_ancestors( indi, as_parent, ancestor_fams, data[f_key] )

for indi in testers:
    for other in blood_related[indi]:
        blood_related[indi][other]['label'] = find_relation_label( blood_related[indi][other] )

within_range = dict()

for indi in testers:
    within_range[indi] = []
    dna_value = testers[indi]
    if options['show-each']:
       print( person_info(indi), 'within range of', dna_value, 'cM', file=sys.stderr )
    for other in blood_related[indi]:
        relation = blood_related[indi][other]['label']
        if relation in dna_ranges:
           if dna_ranges[relation]['min'] <= dna_value <= dna_ranges[relation]['max']:
              within_range[indi].append( other )
              if options['show-each']:
                 print( '   ', person_info(other), blood_related[indi][other]['label'], file=sys.stderr )

    if options['show-each']:
       if not within_range[indi]:
          print( 'No one', file=sys.stderr )
    print( '', file=sys.stderr )

# add them together to find the potential common matches
matches = readgedcom.list_intersection( *list(within_range.values()) )

n_matches = len( matches )

print( 'The intersection of matches has', n_matches, 'people', file=sys.stderr )

if n_matches < 1:
   print( '', file=sys.stderr )
   print( 'No one to draw', file=sys.stderr )
   sys.exit(1)

for indi in matches:
    print( '   ', person_info(indi), file=sys.stderr )

if n_matches >= options['max-results']:
   print( '', file=sys.stderr )
   print( 'Too many people to draw in a tree', file=sys.stderr )
   sys.exit(1)


# To draw the tree, connect people of interest to ancestor families
# and let the drawing program sort it out (Graphviz)
#
# But at some point, at the top of the tree, families doesn't connect to their ancestors.
# In order to know where to stop find the shared ancestor families
# who's partners don't have any shared sncestors from the people of interest.

# step 1: make the list of all families heading to the top

# the testers need to be included
for indi in testers:
    matches.append( indi )

fams_along_paths = dict()
for indi in matches:
    for ancestor_fam in ancestor_fams[indi]:
        fams_along_paths[ancestor_fam] = True

# step 2: list all the shared families of all the people of interest
all_shared_fams = dict()
for indi in matches:
    for them in blood_related[indi]:
        if them in matches and them != indi:
           all_shared_fams[blood_related[indi][them]['closest']] = True



start_dot( make_label( data[i_key], testers ), options['orientation'] )
#dot_labels( data[i_key], data[f_key], testers.keys(), parent_link, partner_to_parent )
#dot_connect( options['reverse'], parent_link, partner_to_parent )
end_dot()
