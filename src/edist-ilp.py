##############################
# ILP program to compute the clustering accuracy of OCR output

# Assumes gold and sys output have the same number of lines

# INPUT: 2 strings from STDIN:
# 1. Gold string: g1 g2 ... gm (tokens separated by space)
# 2. System output: c1 c2 ... cn (cluster names separated by space)

# OUTPUT: Normalized edit distance of the best matching of 1 and 2
# ** no replacements allowed. each replacement is represented by a deletion and an inserstion which results in a cost of 2)
# ** normalized distance = number of edits / max( len(gold), len(sys_out) )

# Author: Nada Aldarrab
# 2017
##############################

import sys
from gurobipy import *

with open(sys.argv[1]) as gold_file:
    gold_lines = gold_file.read().splitlines()

with open(sys.argv[2]) as sys_out_file:
    sys_out_lines = sys_out_file.read().splitlines()


try:

    # Create a new model
    m = Model("accuracy")


    # Create variables
    for line_index in range(0, len(gold_lines)):
        # Lines
        gold = gold_lines[line_index].split()
        sys_out = sys_out_lines[line_index].split()

        # Column 0 and Row 0
        exec('m_0_0_l_{} = m.addVar(vtype=GRB.BINARY, name="m_0_0_l_{}")'.format(line_index, line_index))

        for j in range(1, len(gold)+1):
            exec('i_0_{}_l_{} = m.addVar(vtype=GRB.BINARY, name="i_0_{}_l_{}")'.format(j, line_index, j,line_index))
        for i in range(1, len(sys_out)+1):
            exec('d_{}_0_l_{} = m.addVar(vtype=GRB.BINARY, name="d_{}_0_l_{}")'.format(i, line_index, i, line_index))
        exec('m_{}_{}_l_{} = m.addVar(vtype=GRB.BINARY, name="m_{}_{}_l_{}")'.format(len(sys_out)+1, len(gold)+1, line_index, len(sys_out)+1, len(gold)+1, line_index))

        # Columns 1:n
        for i in range(1, len(sys_out)+1):
            for j in range(1, len(gold)+1):
                exec('i_{}_{}_l_{} = m.addVar(vtype=GRB.BINARY, name="i_{}_{}_l_{}")'.format(i, j, line_index, i, j, line_index))
                exec('m_{}_{}_l_{} = m.addVar(vtype=GRB.BINARY, name="m_{}_{}_l_{}")'.format(i, j, line_index, i, j, line_index))
                exec('d_{}_{}_l_{} = m.addVar(vtype=GRB.BINARY, name="d_{}_{}_l_{}")'.format(i, j, line_index, i, j, line_index))

        # Integrate new variables
        m.update()
        # links
        variables = [v.varName for v in m.getVars()]
        for i in set(sys_out):
            for j in set(gold):
                if 'l_{}_{}'.format(i, j) not in variables:
                    exec('l_{}_{} = m.addVar(vtype=GRB.BINARY, name="l_{}_{}")'.format(i, j, i, j))
        # Integrate new variables
        m.update()


    # Set objective
    matches = [v.varName for v in m.getVars() if v.varName[0]=='m']
    m.setObjective(eval(' + '.join(matches)), GRB.MAXIMIZE)


    # Add Constraints
    variables = [v.varName for v in m.getVars()]
    sys_out_all = ' '.join(sys_out_lines).split()
    gold_all = ' '.join(gold_lines).split()

    # Add constraint 1: Link every cluster to 1 (<=1)
    for i in set(sys_out_all):
        links = ['l_'+i+'_'+j for j in set(gold_all) if 'l_'+i+'_'+j in variables]
        m.addConstr(eval(' + '.join(links)) <= 1)

    # Add constraint 2: Gold could be left out (<=1)
    for j in set(gold_all):
        links = ['l_'+i+'_'+j for i in set(sys_out_all)if 'l_'+i+'_'+j in variables]
        m.addConstr(eval(' + '.join(links)) <= 1)


    # Constraints 3-5
    for line_index in range(0, len(gold_lines)):
        # Lines
        gold = gold_lines[line_index].split()
        sys_out = sys_out_lines[line_index].split()

        # Add constraint 3: Only match if link exists
        for i in range(1, len(sys_out)+1):
            for j in range(1, len(gold)+1):
                exec('m.addConstr(m_{}_{}_l_{} <= l_{}_{})'.format(i, j, line_index, sys_out[i-1], gold[j-1]))

        # Add constraint 4: conservation
        # Column 0
        exec('m.addConstr(m_0_0_l_{} == i_0_1_l_{} + m_1_1_l_{} + d_1_0_l_{})'.format(line_index, line_index, line_index, line_index))
        for j in range(1, len(gold)):
            exec('m.addConstr(i_0_{}_l_{} == i_0_{}_l_{} + m_1_{}_l_{} + d_1_{}_l_{})'.format(j, line_index, j+1, line_index, j+1, line_index, j, line_index))
        exec('m.addConstr(i_0_{}_l_{} == d_1_{}_l_{})'.format(len(gold), line_index, len(gold), line_index))
        # Columns 1:n-1
        for i in range(1, len(sys_out)):
            exec('m.addConstr(d_{}_0_l_{} == i_{}_1_l_{} + m_{}_1_l_{} + d_{}_0_l_{})'.format(i, line_index, i, line_index, i+1, line_index, i+1, line_index))

            for j in range(1, len(gold)):
                exec('m.addConstr(d_{}_{}_l_{} + m_{}_{}_l_{} + i_{}_{}_l_{} == i_{}_{}_l_{} + m_{}_{}_l_{} + d_{}_{}_l_{})'.format(i, j, line_index, i, j, line_index, i, j, line_index, i, j+1, line_index, i+1, j+1, line_index, i+1, j, line_index))

            exec('m.addConstr(d_{}_{}_l_{} + m_{}_{}_l_{} + i_{}_{}_l_{}  == d_{}_{}_l_{})'.format(i, len(gold), line_index, i, len(gold), line_index, i, len(gold), line_index, i+1, len(gold), line_index))
        # Column n
        exec('m.addConstr(d_{}_0_l_{} == i_{}_1_l_{})'.format(len(sys_out), line_index, len(sys_out), line_index))

        for j in range(1, len(gold)):
            exec('m.addConstr(d_{}_{}_l_{} + m_{}_{}_l_{} + i_{}_{}_l_{}  == i_{}_{}_l_{})'.format(len(sys_out), j, line_index, len(sys_out), j, line_index, len(sys_out), j, line_index, len(sys_out), j+1, line_index))

        exec('m.addConstr(d_{}_{}_l_{} + m_{}_{}_l_{} + i_{}_{}_l_{}  == m_{}_{}_l_{})'.format(len(sys_out), len(gold), line_index, len(sys_out), len(gold), line_index, len(sys_out), len(gold), line_index, len(sys_out)+1, len(gold)+1, line_index))

        # Add constraint 5: Initial flow (maximum)
        exec('m.addConstr(m_0_0_l_{} == 1)'.format(line_index))


    m.optimize()

    # Print results
    print('')
    print('#####################')
    print('Results:')
    print('')

    matches = m.objVal-2*len(gold_lines)
    print('Number of matches: %g' % matches)

    # compute edit distance. combine subsequent ins and del to be 1 replacement
    edit_links = [v.varName for v in m.getVars() if (v.varName[0]=='i' or v.varName[0]=='d') and v.x == 1]
    inserts = [link for link in edit_links if link[0]=='i']
    mod_inserts = list(inserts)
    deletes = [link for link in edit_links if link[0]=='d']
    for i in inserts:
        for d in deletes:
            if i.split('_')[2] == d.split('_')[1] and i.split('_')[-1] == d.split('_')[-1]:
                mod_inserts.remove(i)
    edits = len(mod_inserts)+len(deletes)
    replacements = len(inserts)-len(mod_inserts)
    print('Total number of edits: %g' % edits)
    print('Number of replacements: %g' % replacements)
    print('Number of inserts: %g' % len(mod_inserts))
    print('Number of deletes: %g' % (edits-replacements-len(mod_inserts)))
    print('')

    normalized_edit_distance = (float(edits)/max(len(gold_all), len(sys_out_all)))
    print('Normalized edit distance of the best matching: %g' % normalized_edit_distance)
    print('Accuracy: %g' % (1-normalized_edit_distance))
    print('')

    # links
    links = [v.varName for v in m.getVars() if v.varName[0]=='l' and v.x == 1]
    print('number of links: ' + str(len(links)))
    print('')

    # unmatched golds and clusters
    print('links:')
    sys_out_set = list(set(sys_out_all))
    mod_sys_out_set = list(sys_out_set)
    gold_set = list(set(gold_all))
    mod_gold_set = list(gold_set)
    for l in links:
        if(l.split('_')[2] == ''):
            print(l.split('_')[1] + '\t' + '_')
        else:
            print(l.split('_')[1] + '\t' + l.split('_')[2])
        if l.split('_')[1] in sys_out_set:
            mod_sys_out_set.remove(l.split('_')[1])
        if(l.split('_')[2] == '' and '_' in mod_gold_set):
            mod_gold_set.remove('_')
        if l.split('_')[2] in mod_gold_set:
            mod_gold_set.remove(l.split('_')[2])
    print('')
    print('Unmatched gold characters:')
    print(mod_gold_set)
    print('Unmatched clusters:')
    print(mod_sys_out_set)
    print('')
    print('#####################')
    print('')

except GurobiError:
    print('Encountered a Gurobi error')

except AttributeError:
    print('Encountered an attribute error')
