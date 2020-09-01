#!python3

import pandas as pd
import urllib
import xmltodict
import argparse
import xlsxwriter
import time

def write_out(filepath='', wkbk=None, orig=None):
    if wkbk is None:
        raise ValueError('Modified Excel file empty, exiting with failure.')
    elif orig is None:
        raise ValueError('No original Excel file provided when writing, exit with failure.')
    else:
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            for sheet in [sn for sn in orig.sheet_names]:
                wkbk[sheet].to_excel(writer, sheet_name=sheet, engine='xlsxwriter', index = False)
        print("Completed writing file ", filepath)


def AddDescriptions(input_excel="", HMP_name='HMP ID'):
    start = time.time()
    # read the input excel file
    xl_file = pd.ExcelFile(input_excel)
    # make a Python dictionary, each sheet is key'd by name foreach sheet in excel file
    wkbk = {sheet_name: xl_file.parse(sheet_name) for sheet_name in xl_file.sheet_names}

    for sheet_name in wkbk.keys():
        print("Working food: ", sheet_name)

        ## TODO:> Search for column header, assign, then 'restack'

        if HMP_name in wkbk[sheet_name].columns:
            complete_counter = 0
            fail_counter = 0

            nrows = len(wkbk[sheet_name].index)

            id_keys = ['foodb_id', 'chemspider_id', 'pubchem_compound_id',
                     'chebi_id', 'drugbank_id', 'phenol_explorer_compound_id',
                     'knapsack_id', 'kegg_id', 'bigg_id', 'wikipedia_id',
                     'metlin_id', 'biocyc_id', 'pdb_id']

            for external_id in id_keys:
                wkbk[sheet_name][external_id] = pd.Series([""]*nrows,
                                                            index=wkbk[sheet_name].index)

            wkbk[sheet_name]['HMDB_Description'] = pd.Series([""]*nrows,
                                                               index=wkbk[sheet_name].index)               
              
            is_na_value = wkbk[sheet_name].isnull()

            for row_idx in range(0, nrows):
                if is_na_value.loc[row_idx, HMP_name] == False:
                    hmdb_id = wkbk[sheet_name].loc[row_idx, HMP_name]
                    hmdb_id = "HMDB00" + hmdb_id[4::]
                    print("Doing ", hmdb_id)
                    url_str = "https://hmdb.ca/metabolites/"+hmdb_id+".xml"
                    try:
                        with urllib.request.urlopen(url_str) as response:
                            hmdb_xml = response.read()
                            xml_data = xmltodict.parse(hmdb_xml)

                            desc_str = xml_data['metabolite']['description']
                            wkbk[sheet_name].loc[row_idx, 'HMDB_Description'] = desc_str 


                            for external_id in id_keys:
                                if xml_data['metabolite'][external_id] is not None:
                                    val = xml_data['metabolite'][external_id]
                                    wkbk[sheet_name].loc[row_idx, external_id] = val

                            complete_counter = complete_counter + 1

                    except:
                        print(hmdb_id, " FAILED")
                        fail_counter = fail_counter + 1
                        continue

            print("Succeeded: ", complete_counter)
            print("Fail counter: ", fail_counter)
            print("Out of: ", nrows)
        else:
            print("No column ", HMP_name, " in ", sheet_name)

    print("Completed all sheets in: ", time.time() - start, " seconds")

    return wkbk, xl_file


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("input_excel", 
                           help="filepath to input excel workbook",
                           type=str)
    argparser.add_argument("output_excel",
                           help="filepath to write output excel workbook",
                           type=str)
    args = argparser.parse_args()
    #print(args.input_excel)
    res = AddDescriptions(input_excel=args.input_excel,
                          HMP_name='HMP ID')
    write_out(args.output_excel, res[0], res[1])

