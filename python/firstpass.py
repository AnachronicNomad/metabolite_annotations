#!python3

import pandas as pd
import urllib
import xmltodict
import argparse

def AddDescriptions(input_excel="", output_excel="", sheet_name=""):
    # read the input excel file
    xl_file = pd.ExcelFile(input_excel)
    # make a Python dictionary, each sheet is key'd by name foreach sheet in excel file
    wkbk = {sheet_name: xl_file.parse(sheet_name) for sheet_name in xl_file.sheet_names}

    nrows = len(wkbk[sheet_name].index)

    wkbk[sheet_name]['HMDB_Description'] = pd.Series([""]*nrows,
                                                     index=wkbk[sheet_name].index)
    id_keys = ['foodb_id', 'chemspider_id', 'pubchem_compound_id',
               'chebi_id', 'drugbank_id', 'phenol_explorer_compound_id',
               'knapsack_id', 'kegg_id', 'bigg_id', 'wikipedia_id',
               'metlin_id', 'biocyc_id', 'pdb_id']
               
    for external_id in id_keys:
        wkbk[sheet_name][external_id] = pd.Series([""]*nrows,
                                                  index=wkbk[sheet_name].index)
    is_na_value = wkbk[sheet_name].isnull()

    for row_idx in range(0, nrows):
        if is_na_value.loc[row_idx, 'HMP ID'] == False:
            hmdb_id = wkbk[sheet_name].loc[row_idx, 'HMP ID']
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

            except:
                print(hmdb_id, " FAILED")
                continue

    with pd.ExcelWriter(output_excel) as writer:
        for sheet in [sn for sn in xl_file.sheet_names]:
            wkbk[sheet].to_excel(writer, sheet_name=sheet, engine='xlsxwriter')


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("input_excel", 
                           help="filepath to input excel workbook",
                           type=str)
    argparser.add_argument("output_excel",
                           help="filepath to write output excel workbook",
                           type=str)
    argparser.add_argument("sheet_name",
                           help="the name of the excel sheet",
                           type=str)
    args = argparser.parse_args()
    #print(args.input_excel)
    AddDescriptions(input_excel=args.input_excel,
                    output_excel=args.output_excel,
                    sheet_name=args.sheet_name)