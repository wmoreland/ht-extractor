# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

ht_output_file = 'Out_bcflow2'

'''
Dyke    a       b       c
|########@@@@@@@@********    where cell widths are:
|########@@@@@@@@********
|########@@@@@@@@********    dyke to a, # = Da_width
|########@@@@@@@@********    a to b,    @ = ab_width
|########@@@@@@@@********    b to c,    * = bc_width
|########@@@@@@@@********

Enter column numbers of LAST column of given width. If column not needed then
leave as empty list like so: []
Put cell widths in even if the width is 1.
The cell widths can be left with values as they're not used in boolean checks.
'''
a = 42
Da_width = 1

b = 74
ab_width = 2

c = []
bc_width = 1

d = []
cd_width = 1

#%% Extractor #################################################################

# defining switches
switch_x = False
switch_z = False
switch_heat = False

# initialising lists
x = []
x_values = []
z = []
time = []
heat = {}
heat_values = []

with open(ht_output_file) as file_in:  # open ht output file
    lines = filter(None, (line.lstrip() for line in file_in))  # filter out empty lines
    for line in lines:  # loop through all remaining lines
        if 'Simulation Completed' in line:  # stop the data collection
            next(file_in), next(file_in)  # skips the next two lines
            continue
        if 'X-Direction' in line:  # get ready to collect x-direction data by flipping x switch
            switch_x = True
            continue
        if 'Y-Direction' in line:  # stop collecting x-direction data
            switch_x = False
#            if len(x) == 1: # Not sure what this line does..... Seems unnecessary!
            num_columns = max(x)  # find the maximum value in list, i.e. the final column number
        if switch_x:  # if in the x-direction data section
            for item in line.split():  # split the current line up into items deliminated by spaces
                try:  # using try/except because using int on float was throwing error
                    converted_item = int(item)  # convert string to integer
                except:
                    converted_item = float(item)  # convert string to float
                if type(converted_item) is int:  # if the item is an integer then append it to the list
                    x.append(converted_item)
                else:
                    x_values.append(converted_item)
        if 'Z-Direction' in line:  # get ready to collect z-direction data by flipping z switch
            switch_z = True
            continue
        if 'Output' in line:  # stop collecting z-direction data
            switch_z = False
            num_rows = max(z)  # find the maximum value in list, i.e. the final row number
        if switch_z:  # if in the z-direction data section
            for item in line.split():  # split the current line up into items deliminated by spaces
                try:  # using try/except because using int on float was throwing error
                    converted_item = int(item)  # convert string to integer
                except:
                    converted_item = float(item)  # convert string to float
                if type(converted_item) is int:  # if the item is an integer then append it to the list
                    z.append(converted_item)
        if '(yr)' in line:  # find time data
            for item in line.split():
                try:
                    t = float(item)  # extract just the year value
                    heat[t] = []  # populating the heat dictionary with empty lists
                except:
                    continue
            time.append(t)
        if 'Time' in line:
            switch_heat = False  # turn off heat data collection
            heat_values = []  # reset temporary heat list
        if 'erg' in line:  # get ready to collect heat data
            switch_heat = True
            continue
        if switch_heat and line.startswith(str(num_rows)):  # start collecting heat data
            line = line.split(' ', maxsplit=1)  # separates the row number from the rest of the line
            line.pop(0)  # removes the row number
            line = line[0].strip('\n')  # removes newline characters
            line = line.strip()
            line = [line[i:i+12] for i in range(0, len(line), 12)]  # separates the line into equal-length items made up of individual heat values
            for item in line:  # this section converts the values from strings to floats and if empty values are found they are replaced with NAN
                try:
                    lanku = int(item)
                except ValueError:
                    try:
                        item = float(item)
                    except:
                        item = np.nan
                    heat_values.append(item)
            if len(heat_values) == num_columns:  # if the heat_values variable is the correct length then it is assigned to the heat dictionary
                heat[t] = heat_values

#%% Make DataFrame from heat dictionary #######################################
df_raw = pd.DataFrame.from_dict(data=heat, orient='index').sort_index()
df_raw.columns = x
df_raw2 = pd.DataFrame(columns=x)
s = pd.Series(x_values, index=x, name=' ')
df_raw2 = df_raw2.append(s)
df_raw = pd.concat([df_raw2, df_raw])

df_raw.to_csv('{}_cleaned.csv'.format(ht_output_file))

#%% Converter #################################################################
df_con = df_raw.copy()

for column in df_con.columns:
    if not df_con[column].isnull().any():
        df_con.iloc[1:, df_con.columns.get_loc(column)] = df_con.iloc[1:, df_con.columns.get_loc(column)] * (-1e-7)

df_con.to_csv('joules.csv')

#%% Isolator ##################################################################
df_iso = df_con.copy()

if bool(d):
    for column in df_iso.columns:
        if column <= a:
            try:
                df_iso.iloc[1:, df_iso.columns.get_loc(column)] = df_iso.iloc[1:, df_iso.columns.get_loc(column)] - (df_iso.iloc[1:, df_iso.columns.get_loc(c)] / (cd_width / Da_width))
            except:
                print('There was an error isolating the signal in column ', column)
        elif a < column <= b:
            try:
                df_iso.iloc[1:, df_iso.columns.get_loc(column)] = df_iso.iloc[1:, df_iso.columns.get_loc(column)] - (df_iso.iloc[1:, df_iso.columns.get_loc(c)] / (cd_width / ab_width))
            except:
                print('There was an error isolating the signal in column ', column)
        elif b < column <= c:
            try:
                df_iso.iloc[1:, df_iso.columns.get_loc(column)] = df_iso.iloc[1:, df_iso.columns.get_loc(column)] - (df_iso.iloc[1:, df_iso.columns.get_loc(c)] / (cd_width / bc_width))
            except:
                print('There was an error isolating the signal in column ', column)
        elif c < column <= d:
            try:
                df_iso.iloc[1:, df_iso.columns.get_loc(column)] = df_iso.iloc[1:, df_iso.columns.get_loc(column)] - df_iso.iloc[1:, df_iso.columns.get_loc(d)]
            except:
                print('There was an error isolating the signal in column ', column)

#if bool(c) and not bool(d):
#    for column in df_iso.columns:
#        if column <= a:
#            try:
#                df_iso.iloc[1:, df_iso.columns.get_loc(column)] = df_iso.iloc[1:, df_iso.columns.get_loc(column)] - (df_iso.iloc[1:, df_iso.columns.get_loc(c)] / (bc_width / Da_width))
#            except:
#                print('There was an error isolating the signal in column ', column)
#        elif a < column <= b:
#            try:
#                df_iso.iloc[1:, df_iso.columns.get_loc(column)] = df_iso.iloc[1:, df_iso.columns.get_loc(column)] - (df_iso.iloc[1:, df_iso.columns.get_loc(c)] / (bc_width / ab_width))
#            except:
#                print('There was an error isolating the signal in column ', column)
#        elif b < column <= c:
#            try:
#                df_iso.iloc[1:, df_iso.columns.get_loc(column)] = df_iso.iloc[1:, df_iso.columns.get_loc(column)] - df_iso.iloc[1:, df_iso.columns.get_loc(c)]
#            except:
#                print('There was an error isolating the signal in column ', column)
#        elif column > c:
#            try:
#                df_iso.iloc[1:, df_iso.columns.get_loc(column)] = 0.0
#            except:
#                print('There was an error isolating the signal in column ', column)

if not bool(c):
    for column in df_iso.columns:
        if column <= a:
            try:
                df_iso.iloc[1:, df_iso.columns.get_loc(column)] = df_iso.iloc[1:, df_iso.columns.get_loc(column)] - (df_iso.iloc[1:, df_iso.columns.get_loc(b)] / (ab_width / Da_width))
            except:
                print('There was an error isolating the signal in column ', column)
        elif a < column <= b:
            try:
                df_iso.iloc[1:, df_iso.columns.get_loc(column)] = df_iso.iloc[1:, df_iso.columns.get_loc(column)] - df_iso.iloc[1:, df_iso.columns.get_loc(b)]
            except:
                print('There was an error isolating the signal in column ', column)
        elif column > b:
            try:
                df_iso.iloc[1:, df_iso.columns.get_loc(column)] = 0.0
            except:
                print('There was an error isolating the signal in column ', column)

df_iso.to_csv('dyke_signal.csv')

#%% Combinor ##################################################################
with pd.ExcelWriter('output.xlsx') as writer:
    df_raw.to_excel(writer, sheet_name='Raw')
    df_con.to_excel(writer, sheet_name='Converted')
    df_iso.to_excel(writer, sheet_name='Isolated')
