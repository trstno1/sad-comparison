""" Project code for graphing the results of the comparisions for species abundance distribution (SAD) models """

from __future__ import division

import csv
import sys
import multiprocessing
import itertools
import os
import matplotlib.pyplot as plt
import colorsys
import numpy as np
from math import log, exp
from scipy import stats
import sqlite3 as dbapi

from mpl_toolkits.axes_grid.inset_locator import inset_axes

# Function to import the AICc results.
def import_results(datafile):
    """Imports raw result .csv files in the form: site, S, N, AICc_logseries, AICc_logseries_untruncated, AICc_pln, AICc_negbin, AICc_geometric."""
    raw_results = np.genfromtxt(datafile, dtype = "S15, i8, i8, f8, f8, f8, f8, f8", skip_header = 1,
                      names = ['site', 'S', 'N', 'AICc_logseries', 'AICc_logseries_untruncated', 'AICc_pln', 'AICc_negbin', 'AICc_geometric'], delimiter = ",", missing_values = '', filling_values = '', )
    return raw_results

# Function to determine the winning model for each site.
def winning_model(data_dir, dataset_name, results):
    # Open output files
    output_processed = csv.writer(open(data_dir + dataset_name + '_processed_results.csv','wb'))
    # Insert comment line
    output_processed.writerow(["# 0 = Logseries, 1 = Untruncated logseries, 2 = Poisson lognormal, 3 = Negative binomial, 4 = Geometric series"])
    
    # Insert header
    output_processed.writerow(['dataset', 'site', 'S', 'N', "model_code", "AICc_weight_model"])
   
    for site in results:
        site_results = site.tolist()
        site_ID = site_results[0]
        S = site_results[1]
        N = site_results[2]
        AICc_weights = site_results[3:]


        AICc_max_weight = max(AICc_weights) # This will return the actual AICc_weight of the winning model, given that the winning model is the one with the highest AICc weight.

        winning_model = AICc_weights.index(AICc_max_weight) # This will return the winning model, where the model is indicated by the index position
        
        if winning_model == 0:
            model_name = 'Logseries'
            
        elif winning_model == 1:
            model_name = 'Untruncated logseries'
            
        elif winning_model == 2:
            model_name = 'Poisson lognormal'
            
        elif winning_model == 3:
            model_name = 'Negative binomial'
            
        else:
            model_name = 'Geometric series'

        # Format results for output
        processed_results = [[dataset_name] + [site_ID] + [S] + [N] + [winning_model] + [model_name] + [AICc_max_weight]]
        
                                        
        # Save results to a csv file:            
        output_processed.writerows(processed_results)
        
        # Save results to sqlite database      
        #Create database for simulated data """
        cur.execute("""CREATE TABLE IF NOT EXISTS ResultsWin
                       (dataset_code TEXT,
                        site TEXT,
                        S INTEGER,
                        N INTEGER,
                        model_code INTEGER,
                        model_name TEXT,
                        AICc_weight_model FLOAT)""")
           
        cur.executemany("""INSERT INTO ResultsWin VALUES(?,?,?,?,?,?,?)""", processed_results)
        con.commit()
        
    return processed_results
        
def process_results(data_dir, dataset_name, results, value_type):
    for site in results:
        site_results = site.tolist()
        site_ID = site_results[0]
        S = site_results[1]
        N = site_results[2]
        values = site_results[3:]
        counter = 0
        

        for index, value in enumerate(values):
            if index == 0:
                model_name = 'Logseries'
                processed_results = [[dataset_name] + [site_ID] + [S] + [N] + [index] + [model_name] + [value_type] + [value]]
            
            elif index == 1:
                model_name = 'Untruncated logseries'
                processed_results = [[dataset_name] + [site_ID] + [S] + [N] + [index] + [model_name] + [value_type] + [value]]
            
            elif index == 2:
                model_name = 'Poisson lognormal'
                processed_results = [[dataset_name] + [site_ID] + [S] + [N] + [index] + [model_name] + [value_type] + [value]]
            
            elif index == 3:
                model_name = 'Negative binomial'
                processed_results = [[dataset_name] + [site_ID] + [S] + [N] + [index] + [model_name] + [value_type] + [value]]
            
            else:
                model_name = 'Geometric series'
                processed_results = [[dataset_name] + [site_ID] + [S] + [N] + [index] + [model_name] + [value_type] + [value]]

            # Save results to sqlite database      
            #Create database for simulated data """
            cur.execute("""CREATE TABLE IF NOT EXISTS RawResults
                       (dataset_code TEXT,
                        site TEXT,
                        S INTEGER,
                        N INTEGER,
                        model_code INTEGER,
                        model_name TEXT,
                        value_type TEXT,
                        value FLOAT)""")
           
            print(processed_results)
            cur.executemany("""INSERT INTO RawResults VALUES(?,?,?,?,?,?,?,?)""", processed_results)
            con.commit()
        
    return processed_results   
# Set up analysis parameters
data_dir = './sad-data/' # path to data directory
results_ext = '_dist_test.csv' # Extension for raw model AICc results files
likelihood_ext = '_likelihoods.csv' # Extension for raw model likelihood files

datasets = ['bbs', 'cbc', 'fia', 'gentry', 'mcdb', 'naba'] # Dataset ID codes

# Asks for toggle variable so I don't have to rerun all the setup if it is already processed.
needs_processing = input("Data needs to be processed into an sqlite database, True or False?  ")  
#needs_processing = False # THIS LINE IS TEMPORARY AND NEEDS TO BE DELETED IN THE FINAL PRODUCT.

# Starts actual processing for each set of results in turn.
if needs_processing == True:
    # Set up database capabilities 
    # Set up ability to query data
    con = dbapi.connect('./sad-data/SummarizedResults.sqlite')
    cur = con.cursor()
    
    # Switch con data type to string
    con.text_factory = str    
    cur.execute("""DROP TABLE IF EXISTS ResultsWin""")
    cur.execute("""DROP TABLE IF EXISTS RawResults""")
    con.commit() 
    for dataset in datasets:
        datafile = data_dir + dataset + results_ext
        datafile2 = data_dir + dataset + likelihood_ext
        
        raw_results = import_results(datafile) # Import data
        
        raw_results_likelihood = import_results(datafile2) # Import data

        winning_model(data_dir, dataset, raw_results) # Finds the winning model for each site
        
        process_results(data_dir, dataset, raw_results, 'AICc weight') #Turns the raw results into a database.
        process_results(data_dir, dataset, raw_results_likelihood, 'likelihood') #Turns the raw results into a database.
        
    
    #Close connection to database
    con.close()    

# Summarize the number of wins for each model/dataset
# Set up database capabilities 
# Set up ability to query data
con = dbapi.connect('./sad-data/SummarizedResults.sqlite')
cur = con.cursor()

# Switch con data type to string
con.text_factory = str




# Make histogram
# Set up figure
total_wins_fig= plt.figure()

# Extract number of wins for all datasets combined.
total_wins = cur.execute("""SELECT model_name, COUNT(model_code) AS total_wins FROM ResultsWin
                            GROUP BY model_code""")

total_wins = cur.fetchall()


# Plot variables for total wins
N = len(total_wins)
x = np.arange(1, N+1)
y = [ num for (s, num) in total_wins ]
labels = [ s for (s, num) in total_wins ]
width = 1
bar1 = plt.bar( x, y, width, color="grey" )
plt.ylabel( 'Number of Wins' )
plt.xticks(x + width/2.0, labels, fontsize = 'small' )
plt.xlabel( 'Species abundance distribution models' )
plt.show()


#Output figure
fileName = "./sad-data/total_wins.png"
plt.savefig(fileName, format="png" )




# Extract number of wins for each model and dataset
# BBS
bbs_wins  = cur.execute("""SELECT model_name, COUNT(model_code) AS total_wins FROM ResultsWin
                                 WHERE dataset_code == 'bbs'
                                 GROUP BY model_code""")
           
bbs_wins = cur.fetchall()

#CBC
cbc_wins = g= cur.execute("""SELECT model_name, COUNT(model_code) AS total_wins FROM ResultsWin
                                 WHERE dataset_code == 'cbc'
                                 GROUP BY model_code""")
           
cbc_wins = cur.fetchall()

#FIA
fia_wins = cur.execute("""SELECT model_name, COUNT(model_code) AS total_wins FROM ResultsWin
                                 WHERE dataset_code == 'fia'
                                 GROUP BY model_code""")
           
fia_wins = cur.fetchall()

#Gentry
gentry_wins = cur.execute("""SELECT model_name, COUNT(model_code) AS total_wins FROM ResultsWin
                                 WHERE dataset_code == 'gentry'
                                 GROUP BY model_code""")
           
gentry_wins = cur.fetchall()

#MCDB
mcdb_wins = cur.execute("""SELECT model_name, COUNT(model_code) AS total_wins FROM ResultsWin
                                 WHERE dataset_code == 'mcdb'
                                 GROUP BY model_code""")
           
mcdb_wins = cur.fetchall()

#NABA
naba_wins = cur.execute("""SELECT model_name, COUNT(model_code) AS total_wins FROM ResultsWin
                                 WHERE dataset_code == 'naba'
                                 GROUP BY model_code""")
           
naba_wins = cur.fetchall()

# Make histogram
# Set up figure
wins_by_dataset_fig = plt.figure()


# Plot variables for bbs subplot
plt.subplot(3,2,1)
N = len(bbs_wins)
x = np.arange(1, N+1)
y = [ num for (s, num) in bbs_wins ]
labels = [ s for (s, num) in bbs_wins ]
width = 1
bar1 = plt.bar( x, y, width, color="red" )
plt.yticks(fontsize = 'small')
plt.ylabel( 'Number of Wins', fontsize = 'small')
plt.xticks(x + width/2.0, labels, fontsize = 5.9 )
plt.xlabel( 'BBS' )


# Plot variables for cbc subplot
plt.subplot(3,2,2)
N = len(cbc_wins)
x = np.arange(1, N+1)
y = [ num for (s, num) in cbc_wins ]
labels = [ s for (s, num) in cbc_wins ]
width = 1
bar1 = plt.bar( x, y, width, color="orange" )
plt.yticks(fontsize = 'small')
plt.ylabel( 'Number of Wins', fontsize = 'small' )
plt.xticks(x + width/2.0, labels, fontsize = 5.9  )
plt.xlabel( 'CBC' )


# Plot variables for fia subplot
plt.subplot(3,2,3)
N = len(fia_wins)
x = np.arange(1, N+1)
y = [ num for (s, num) in fia_wins ]
labels = [ s for (s, num) in fia_wins ]
width = 1
bar1 = plt.bar( x, y, width, color="green" )
plt.yticks(fontsize = 'small')
plt.ylabel( 'Number of Wins', fontsize = 'small' )
plt.xticks(x + width/2.0, labels, fontsize = 5  )
plt.xlabel( 'FIA' )


# Plot variables for Gentry subplot
plt.subplot(3,2,4)
N = len(gentry_wins)
x = np.arange(1, N+1)
y = [ num for (s, num) in gentry_wins ]
labels = [ s for (s, num) in gentry_wins ]
width = 1
bar1 = plt.bar( x, y, width, color="olivedrab" )
plt.yticks(fontsize = 'small')
plt.ylabel( 'Number of Wins', fontsize = 'small' )
plt.xticks(x + width/2.0, labels, fontsize = 5.9  )
plt.xlabel( 'Gentry' )


# Plot variables for mcdb subplot
plt.subplot(3,2,5)
N = len(mcdb_wins)
x = np.arange(1, N+1)
y = [ num for (s, num) in mcdb_wins ]
labels = [ s for (s, num) in mcdb_wins ]
width = 1
bar1 = plt.bar( x, y, width, color="sienna" )
plt.yticks(fontsize = 'small')
plt.ylabel( 'Number of Wins', fontsize = 'small' )
plt.xticks(x + width/2.0, labels, fontsize = 5  )
plt.xlabel( 'MCDB' )



# Plot variables for NABA subplot
plt.subplot(3,2,6)
N = len(naba_wins)
x = np.arange(1, N+1)
y = [ num for (s, num) in naba_wins ]
labels = [ s for (s, num) in naba_wins ]
width = 1
bar1 = plt.bar( x, y, width, color="blue" )
plt.yticks(fontsize = 'small')
plt.ylabel( 'Number of Wins', fontsize = 'small' )
plt.xticks(x + width/2.0, labels, fontsize = 5.9  )
plt.xlabel( 'NABA' )

plt.tight_layout()
plt.show()



#Output figure
fileName = "./sad-data/wins_by_dataset.png"
plt.savefig(fileName, format="png" )



#AIC_c weight distributions graphs
# Make histogram
# Set up figure
AIC_c_weights = plt.figure()

# Extract AICc weights for each model.
logseries = cur.execute("""SELECT model_name, value FROM RawResults
                            WHERE model_name == 'Logseries' AND value_type =='AICc weight' AND value IS NOT NULL
                            ORDER BY value""")
logseries = cur.fetchall()


untruncated_logseries = cur.execute("""SELECT model_name, value FROM RawResults
                            WHERE model_name =='Untruncated logseries' AND value_type =='AICc weight' AND value IS NOT NULL
                            ORDER BY value""")
untruncated_logseries = cur.fetchall()


pln = cur.execute("""SELECT model_name, value FROM RawResults
                            WHERE model_name =='Poisson lognormal' AND value_type =='AICc weight' AND value IS NOT NULL
                            ORDER BY value""")
pln = cur.fetchall()
                  
                            
                            
neg_bin = cur.execute("""SELECT model_name, value FROM RawResults
                            WHERE model_name =='Negative binomial' AND value_type =='AICc weight' AND value IS NOT NULL
                            ORDER BY value""")
neg_bin = cur.fetchall()
                      
                            
geometric = cur.execute("""SELECT model_name, value FROM RawResults
                            WHERE model_name =='Geometric series' AND value_type =='AICc weight' AND value IS NOT NULL
                            ORDER BY value""")
geometric = cur.fetchall()


# Plot variables for weights
bins = 50

model0 = [ num for (s, num) in logseries ]
plt.hist(model0, bins, range = (0,1), facecolor = 'magenta', histtype="stepfilled", alpha=1, label = "Logseries")

model1 = [ num for (s, num) in untruncated_logseries]
plt.hist(model1, bins, range = (0,1), facecolor = 'orange', histtype="stepfilled", alpha=.7, label = "Untruncated logseries")

model2 = [ num for (s, num) in pln]
plt.hist(model2, bins, range = (0,1), facecolor = 'teal', histtype="stepfilled", alpha=.7, label = "Poisson lognormal")

model3 = [ num for (s, num) in neg_bin]
plt.hist(model3, bins, range = (0,1), facecolor = 'gray', histtype="stepfilled", alpha=.7, label = "Negative binomial")

model4 = [ num for (s, num) in geometric]
plt.hist(model4, bins, range = (0,1), facecolor = 'olivedrab', histtype="stepfilled", alpha=.7, label = "Geometric")

plt.legend(loc = 'upper right', fontsize = 11)

plt.xlabel("AICc weights")
plt.ylabel("Frequency")

plt.tight_layout()
plt.show()

#Output figure
fileName = "./sad-data/AICc_weights.png"
plt.savefig(fileName, format="png" )

# Plot weights for each model individually
bins = 50

# Set up figures
plt.figure()
plt.hist(model0, bins, range = (0,1), facecolor = 'magenta', histtype="stepfilled", alpha=1, label = "Logseries")
plt.xlabel("Logseries AICc weights")
plt.ylabel("Frequency")

plt.tight_layout()
plt.show()

#Output figure
fileName = "./sad-data/Logseries_weights.png"
plt.savefig(fileName, format="png" )

plt.figure()
plt.hist(model1, bins, range = (0,1), facecolor = 'orange', histtype="stepfilled", alpha=.7, label = "Untruncated logseries")
plt.xlabel("Untruncated logseries AICc weights")
plt.ylabel("Frequency")

plt.tight_layout()
plt.show()

#Output figure
fileName = "./sad-data/Untruncated logseries_weights.png"
plt.savefig(fileName, format="png" )


plt.figure()
plt.hist(model2, bins, range = (0,1), facecolor = 'teal', histtype="stepfilled", alpha=.7, label = "Poisson lognormal")
plt.xlabel("Poisson lognormal AICc weights")
plt.ylabel("Frequency")

plt.tight_layout()
plt.show()

#Output figure
fileName = "./sad-data/Poisson lognormal_weights.png"
plt.savefig(fileName, format="png" )


plt.figure()
model3 = [ num for (s, num) in neg_bin]
plt.hist(model3, bins, range = (0,1), facecolor = 'gray', histtype="stepfilled", alpha=.7, label = "Negative binomial")
plt.xlabel("Negative binomial AICc weights")
plt.ylabel("Frequency")

plt.tight_layout()
plt.show()

#Output figure
fileName = "./sad-data/Negative binomial_weights.png"
plt.savefig(fileName, format="png" )


plt.figure()
model4 = [ num for (s, num) in geometric]
plt.hist(model4, bins, range = (0,1), facecolor = 'olivedrab', histtype="stepfilled", alpha=.7, label = "Geometric")

plt.xlabel("Geometric AICc weights")
plt.ylabel("Frequency")

plt.tight_layout()
plt.show()

#Output figure
fileName = "./sad-data/Geometric_weights.png"
plt.savefig(fileName, format="png" )


#Likelihood graph
# Make histogram
# Set up figure
l_likelihood = plt.figure()

# Extract AICc weights for each model.
ll_logseries = cur.execute("""SELECT model_name, value FROM RawResults
                            WHERE model_name == 'Logseries' AND value_type =='likelihood' AND value > 0
                            ORDER BY value""")
ll_logseries = cur.fetchall()


ll_untruncated_logseries = cur.execute("""SELECT model_name, value FROM RawResults
                            WHERE model_name =='Untruncated logseries' AND value_type =='likelihood' AND value > 0
                            ORDER BY value""")
ll_untruncated_logseries = cur.fetchall()



ll_pln = cur.execute("""SELECT model_name, value FROM RawResults
                            WHERE model_name =='Poisson lognormal' AND value_type =='likelihood' AND value > 0
                            ORDER BY value""")
ll_pln = cur.fetchall()
                     
                            
                            
ll_neg_bin = cur.execute("""SELECT model_name, value FROM RawResults
                            WHERE model_name =='Negative binomial' AND value_type =='likelihood' AND value > 0
                            ORDER BY value""")
ll_neg_bin = cur.fetchall()


                      
                            
ll_geometric = cur.execute("""SELECT model_name, value FROM RawResults
                            WHERE model_name =='Geometric series' AND value_type =='likelihood' AND value > 0
                            ORDER BY value""")
ll_geometric = cur.fetchall()



# Plot variables for weights
bins = 50

ll_model0 = [ num for (s, num) in ll_logseries ]
plt.hist(ll_model0, bins, facecolor = 'magenta', histtype="stepfilled", alpha=1, label = "Logseries")

ll_model1 = [ num for (s, num) in ll_untruncated_logseries]
plt.hist(ll_model1, bins, facecolor = 'orange', histtype="stepfilled", alpha=.7, label = "Untruncated logseries")

ll_model2 = [ num for (s, num) in ll_pln]
plt.hist(ll_model2, bins, facecolor = 'teal', histtype="stepfilled", alpha=.7, label = "Poisson lognormal")

ll_model3 = [ num for (s, num) in ll_neg_bin]
plt.hist(ll_model3, bins, facecolor = 'gray', histtype="stepfilled", alpha=.7, label = "Negative binomial")

ll_model4 = [ num for (s, num) in ll_geometric]
plt.hist(ll_model4, bins, facecolor = 'olivedrab', histtype="stepfilled", alpha=.7, label = "Geometric")

plt.legend(loc = 'upper right', fontsize = 11)

plt.xlabel("Log-likelihoods")
plt.ylabel("Frequency")

plt.tight_layout()
plt.show()

#Output figure
fileName = "./sad-data/likelihoods.png"
plt.savefig(fileName, format="png" )

# Plot likelihoods for each model individually
plt.figure()
plt.hist(ll_model0, bins, facecolor = 'magenta', histtype="stepfilled", alpha=1, label = "Logseries")
plt.xlabel("Logseries log-likelihoods")
plt.ylabel("Frequency")

plt.tight_layout()
plt.show()

#Output figure
fileName = "./sad-data/logseries_likelihoods.png"
plt.savefig(fileName, format="png" )


plt.hist(ll_model1, bins, facecolor = 'orange', histtype="stepfilled", alpha=.7, label = "Untruncated logseries")
plt.xlabel("Untruncated logseries log-likelihoods")
plt.ylabel("Frequency")

plt.tight_layout()
plt.show()

#Output figure
fileName = "./sad-data/untruncated_logseries_likelihoods.png"
plt.savefig(fileName, format="png" )


plt.hist(ll_model2, bins, facecolor = 'teal', histtype="stepfilled", alpha=.7, label = "Poisson lognormal")
plt.xlabel("Poisson lognormal log-likelihoods")
plt.ylabel("Frequency")

plt.tight_layout()
plt.show()

#Output figure
fileName = "./sad-data/pln_likelihoods.png"
plt.savefig(fileName, format="png" )


plt.hist(ll_model3, bins, facecolor = 'gray', histtype="stepfilled", alpha=.7, label = "Negative binomial")
plt.xlabel("Negative binomial log-likelihoods")
plt.ylabel("Frequency")

plt.tight_layout()
plt.show()

#Output figure
fileName = "./sad-data/neg_bin_likelihoods.png"
plt.savefig(fileName, format="png" )


plt.hist(ll_model4, bins, facecolor = 'olivedrab', histtype="stepfilled", alpha=.7, label = "Geometric")
plt.xlabel("Geometric log-likelihoods")
plt.ylabel("Frequency")

plt.tight_layout()
plt.show()

#Output figure
fileName = "./sad-data/geometric_likelihoods.png"
plt.savefig(fileName, format="png" )

# Close connection
con.close()
