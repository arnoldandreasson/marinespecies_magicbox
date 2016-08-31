#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Copyright (c) 2016 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
#
from __future__ import unicode_literals

import plankton_utils

class WormsMarineSpecies(object):
    """ Utility for WoRMS access. 
        WoRMS, World Register of Marine Species. http://marinespecies.org """

    def __init__(self):
        """ """
        self._worms_ws = plankton_utils.WormsWebservice()

    def generate_tree_from_species_list(self,
                                       in_file_path = '../test_data',
                                       in_file_name = 'worms_indata.txt',
                                       out_file_path = '../test_data',
                                       out_file_name = 'worms_outdata.txt',
                                       out_translate_file_path = '../test_data',
                                       out_translate_file_name = 'translate_taxa.txt',
                                       out_errors_file_path = '../test_data',
                                       out_errors_file_name = 'error_log.txt',
                                       in_scientific_name_column = 'scientific_name',
                                       in_rank_column = 'rank',
                                       in_taxon_id_column = 'taxon_id', # To be used for homonym problems.
                                       ):
        """ """
        # Indata file.
        tablefilereader = plankton_utils.TableFileReader(
            file_path = in_file_path,
            text_file_name = in_file_name,
#             select_columns_by_name = [in_scientific_name_column, in_rank_column, in_taxon_id_column]                
            select_columns_by_name = [in_scientific_name_column, in_taxon_id_column]                
            )
        # Outdata file.
        tablefilewriter = plankton_utils.TableFileWriter(
            file_path = out_file_path,
            text_file_name = out_file_name,
            )
        # Create translate file if valid taxa differ.
        translatefilewriter = plankton_utils.TableFileWriter(
            file_path = out_translate_file_path,
            text_file_name = out_translate_file_name,
            )
        # Log errors.
        errorfilewriter = plankton_utils.TableFileWriter(
            file_path = out_errors_file_path,
            text_file_name = out_errors_file_name,
            )
        #
        taxa_dict = {} # taxon_id: {taxon_id: '', scientific_name: '', rank: '', parent_id: '', etc.}
        translate_dict = {} # taxon_id: {scientific_name_from: '', scientific_name_to: ''}
        error_log_rows = []
        #
        for row_index, row in enumerate(tablefilereader.rows()):
            scientific_name = row[0].strip()
#             rank = row[1]
#             taxon_id = row[2]
            taxon_id = row[1].strip()
            #
            print('WoRMS-'+ unicode(row_index) + ': ' + scientific_name)
            #
            # Species names should contain at least one space.
            # Also process taxa with AphiaID specified.
            if (' ' in scientific_name.strip()) or taxon_id:
#           if rank == 'Species':
                #
                species_dict = None
                try:
                    if taxon_id:
                        # Use AphiaID first, if specified.
                        species_dict = self.get_aphia_name_by_id(taxon_id.replace('AphiaID:', '').strip())
                    else:
                        # Lookup by species name.
                        species_dict = self.find_valid_taxon(scientific_name)
#                     species_dict = self.find_valid_taxon(scientific_name, rank)
                except Exception as e:
                    print('Exception: ' + unicode(e))
                #
#                 if species_dict is None:
#                     if taxon_id:
#                         species_dict = self.get_aphia_name_by_id(taxon_id.replace('AphiaID:', '').strip())
                #
                if species_dict is None:
                    error_log_rows.append(['Species not in WoRMS: ', scientific_name])
                    print(error_log_rows[-1])
                else:
                    # Check if valid name. Add to translate list if not.
                    scientificname = species_dict['scientificname']
                    if scientificname != scientific_name:
                        translate_dict[scientific_name] = scientificname
                    #
                    species_id = species_dict['AphiaID']
                    taxa_dict[species_id] = species_dict
                    # Iterate over classification. Create taxa and classification info string.
                    worms_classification_list = self._worms_ws.get_aphia_classification_by_id(species_id)
                    parent_id = None
                    parent_name = ''
                    classification_strings = []
                    for taxon in worms_classification_list:
                        taxon_id = taxon['AphiaID']
                        classification_strings.append('[' + taxon['rank'] +'] ' + taxon['scientificname'])
                        if taxon_id not in taxa_dict:
                            taxa_dict[taxon_id] = taxon
                            taxa_dict[taxon_id]['classification'] = ' - '.join(classification_strings)
                            if parent_id:
                                taxa_dict[taxon_id]['parent_name'] = parent_name
                                taxa_dict[taxon_id]['parent_id'] = parent_id
                        parent_name = taxon['scientificname']
                        parent_id = taxon['AphiaID']
                    # The last one is the species parent.
                    taxa_dict[species_id]['parent_name'] = parent_name
                    taxa_dict[species_id]['parent_id'] = parent_id
                    # Note: This is not a part of the classification, but useful.
                    classification_strings.append('[' + species_dict['rank'] +'] ' + species_dict['scientificname'])
                    taxa_dict[species_id]['classification'] = ' - '.join(classification_strings) 
        #
        table_header = ['scientific_name', 'rank', 'aphia_id', 'parent_name', 'parent_id', 'classification']
        table_rows = []
        for row in taxa_dict.values():
            outrow = []
            for item in ['scientificname', 'rank', 'AphiaID', 'parent_name', 'parent_id', 'classification']:
                outrow.append(unicode(row.get(item, '')))
            table_rows.append(outrow)
        #
        tablefilewriter.write_file(table_header, table_rows)
        #
        translate_rows = [[k, v] for k,v in translate_dict.items()]
        translatefilewriter.write_file(['species_name_from', 'species_name_to'], translate_rows)
        #
        errorfilewriter.write_file(['errors'], error_log_rows)


    def find_valid_taxon(self, 
                         scientific_name, 
                         rank = None): # Used to reduce some homonym problems.
        """ """
        worms_records = self._worms_ws.get_aphia_records(scientific_name, 
                                                        like='false', 
                                                        fuzzy='false', 
                                                        marine_only='false', 
                                                        offset = 1, 
                                                        )
        number_of_matches = 0
        accepted_taxon = None
        for taxon in worms_records:
            if taxon.get('status', '') == 'accepted':
                if rank:
                    if taxon.get('rank', '') == rank:
                        accepted_taxon = taxon
                        number_of_matches += 1
                else:
                    accepted_taxon = taxon
                    number_of_matches += 1
        # Checck if synonym.
        if not accepted_taxon:
            for taxon in worms_records:
                if taxon.get('status', '') == 'unaccepted':
#                 if taxon.get('unacceptreason', '') == 'synonym':
                    valid_records = self._worms_ws.get_aphia_records(taxon.get('valid_name', ''), 
                                                                    like='false', 
                                                                    fuzzy='false', 
                                                                    marine_only='false', 
                                                                    offset = 1, 
                                                                    )
                    for valid_taxon in valid_records:
                        if valid_taxon.get('status', '') == 'accepted':
                            accepted_taxon = valid_taxon
                            number_of_matches += 1
        #
        if number_of_matches == 0:
            raise UserWarning('No taxa matched. Scientific name: ' + scientific_name)
        if number_of_matches > 1:
            raise UserWarning('Multiple taxa matched. Scientific name: ' + scientific_name)
        #
        return accepted_taxon

    def get_aphia_name_by_id(self, taxon_id):
        """ """
        worms_record = self._worms_ws.get_aphia_record_by_id(taxon_id)

        if not worms_record:
            raise UserWarning('No taxa matched. AphiaID: ' + taxon_id)
        #
        return worms_record

    def generate_worms_info_table(self,
                                  in_file_path = '../test_data',
                                  in_file_name = 'worms_indata.txt',
                                  out_file_path = '../test_data',
                                  out_file_name = 'worms_outdata.txt',
#                                   translate_file_path = '../test_data',
#                                   translate_file_name = 'translate_taxa.txt',
#                                   errors_file_path = '../test_data',
#                                   errors_file_name = 'error_log.txt',
                                  in_scientific_name_column = 'scientific_name',
                                  in_taxon_id_column = 'aphia_id', # To be used for homonym problems.
                                  ):
        """ """
        # Indata file.
        tablefilereader = plankton_utils.TableFileReader(
            file_path = in_file_path,
            text_file_name = in_file_name,
            select_columns_by_name = [in_scientific_name_column, in_taxon_id_column]                
            )
        # Outdata file.
        tablefilewriter = plankton_utils.TableFileWriter(
            file_path = out_file_path,
            text_file_name = out_file_name,
            )
        #
        out_header_list = [
            'worms_status',
            'worms_unaccept_reason',
            'worms_valid_name',
            'worms_valid_authority',
            'worms_rank',
            'worms_kingdom',
            'worms_phylum',
            'worms_class',
            'worms_order',
            'worms_family',
            'worms_genus',
            'worms_scientific_name',
            'worms_authority',
            'worms_url',
            'worms_lsid',
            'worms_aphia_id',
            'worms_valid_aphia_id',
            'worms_citation',
            'worms_classification', # From worms_classification_list.
            'worms_synonyms', # From worms_synonym_list.
            ]
        #
        out_rows = []
        #
        for row_index, row in enumerate(tablefilereader.rows()):
            scientific_name = row[0]
            aphia_id = row[1]
            #
            print('WoRMS-'+ unicode(row_index) + ': ' + scientific_name + ': ' + aphia_id)
            #
            worms_dict = self.create_worms_dict(scientific_name, aphia_id)
            #
            print('WoRMS-info: '+ unicode(worms_dict))
            
            out_row = []
            out_row.append(scientific_name)
            out_row.append(aphia_id)
            for item in out_header_list:
                if item == 'worms_classification':
                    classification = ' - '.join(worms_dict.get('worms_classification_list', []))
                    out_row.append(classification)                     
                elif item == 'worms_synonyms':
                    synonyms = ' - '.join(worms_dict.get('worms_synonym_list', []))
                    out_row.append(synonyms) 
                else:
                    out_row.append(worms_dict.get(item))
            #
            out_rows.append(out_row)
        # Write to file.
        tablefilewriter.write_file(['scientific_name', 'aphia_id'] + out_header_list, out_rows)



    def create_worms_dict(self, scientific_name, 
                                aphia_id = None):
        """ """
        worms_dict = {}
        # GetAphia ID.
        if not aphia_id:
            aphia_id = self._worms_ws.get_aphia_id(scientific_name, marine_only = 'false')
        #
        if not aphia_id:
            # Failed to get info.
            return worms_dict
        #
        # Aphia record.
#         aphia_dict = self.get_aphia_record_by_id(aphia_id)
        aphia_dict = self._worms_ws.get_aphia_record_by_id(aphia_id)
        if not aphia_dict:
            return worms_dict           
        #

        print(unicode(aphia_dict))

        worms_dict['worms_status'] = aphia_dict.get( 'status', '')
        worms_dict['worms_unaccept_reason'] = aphia_dict.get('unacceptreason', '')
 
        worms_dict['worms_valid_name'] = aphia_dict.get('valid_name', '')
        worms_dict['worms_valid_authority'] = aphia_dict.get('valid_authority', '')
 
        worms_dict['worms_rank'] = aphia_dict.get('rank', '')
 
        worms_dict['worms_kingdom'] = aphia_dict.get('kingdom', '')
        worms_dict['worms_phylum'] = aphia_dict.get('phylum', '')
        worms_dict['worms_class'] = aphia_dict.get('class', '')
        worms_dict['worms_order'] = aphia_dict.get('order', '')
        worms_dict['worms_family'] = aphia_dict.get('family', '')
        worms_dict['worms_genus'] = aphia_dict.get('genus', '')
        worms_dict['worms_scientific_name'] = aphia_dict.get('scientificname', '')
        worms_dict['worms_authority'] = aphia_dict.get('authority', '')

        worms_dict['worms_url'] = aphia_dict.get('url', '')
        worms_dict['worms_lsid'] = aphia_dict.get('lsid', '')
        worms_dict['worms_aphia_id'] = aphia_dict.get('AphiaID', '')
        worms_dict['worms_valid_aphia_id'] = aphia_dict.get('valid_AphiaID', '')
         
        worms_dict['worms_citation'] = aphia_dict.get('citation', '')
         
        # Classification. 
        classification_list = []
        parent_list = self._worms_ws.get_aphia_classification_by_id(aphia_id)
        for parent in parent_list:    
            classification_list.append('[' + unicode(parent.get('rank', '')) + '] ' + unicode(parent.get('scientificname', '')))
        #
        worms_dict['worms_classification_list'] = classification_list
         
        # Synonyms.
        synonym_list = []
        synonyms = self._worms_ws.get_aphia_synonyms_by_id(aphia_id)
        if synonyms:
            for synonym in synonyms:
                if (synonym.get('scientificname', '') and synonym.get('authority', '')):
                    synonym_list.append(unicode(synonym.get('scientificname', '')) + ' ' + unicode(synonym.get('authority', '')))
        worms_dict['worms_synonym_list'] = synonym_list
        #        
        return worms_dict



# ===== TEST =====
if __name__ == "__main__":
    """ Used for testing. """
 
    # === Test WormsMarineSpecies. ===
 
    print('\n=== Test WormsMarineSpecies ===')
 
    marinespecies = WormsMarineSpecies()
     
#     try:
#         print('\nTest. WormsMarineSpecies: generate_tree_from_species_list:')
#         worms_result = marinespecies.generate_tree_from_species_list()
#     except Exception as e:
#         print('Test failed: ' + unicode(e))
#         raise

    try:
        print('\nTest. WormsMarineSpecies: generate_worms_info_table:')
        worms_result = marinespecies.generate_worms_info_table()
    except Exception as e:
        print('Test failed: ' + unicode(e))
        raise
