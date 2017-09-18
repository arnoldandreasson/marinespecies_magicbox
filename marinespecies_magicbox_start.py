#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Copyright (c) 2015-2016 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
#
from __future__ import unicode_literals

import plankton_utils

class PtbxMagicBox(object):
    """ Plankton Toolbox Magic Box. """

    def __init__(self):
        """ """
        self._marinespecies = plankton_utils.WormsMarineSpecies()

    def execute(self):
        """ """
#         self._marinespecies.generate_tree_from_species_list(
#                                        in_file_path = 'data',
#                                        in_file_name = 'indata_species_list.txt',
#                                        out_file_path = 'data',
#                                        out_file_name = 'taxa_worms_YYYY-MM-DD.txt',
#                                        out_translate_file_path = 'data',
#                                        out_translate_file_name = 'translate_worms_YYYY-MM-DD.txt',
#                                        out_errors_file_path = 'data',
#                                        out_errors_file_name = 'error_log_worms_YYYY-MM-DD.txt',
#                                        in_scientific_name_column = 'scientific_name',
# #                                        in_rank_column = 'rank',
#                                        in_taxon_id_column = 'aphia_id', # To be used for homonym problems.
#                                        )

        self._marinespecies.generate_worms_info_table(
                                  in_file_path = 'data',
                                  in_file_name = 'indata_species_list.txt',
                                  out_file_path = 'data',
                                  out_file_name = 'worms_outdata.txt',
#                                   translate_file_path = '../test_data',
#                                   translate_file_name = 'translate_taxa.txt',
#                                   errors_file_path = '../test_data',
#                                   errors_file_name = 'error_log.txt',
                                  in_scientific_name_column = 'scientific_name',
                                  in_taxon_id_column = 'aphia_id', # To be used for homonym problems.
                                  )


# ===== TEST =====

if __name__ == "__main__":
    """ """
    print('\n=== Started. ===')
    magicbox = PtbxMagicBox()
    try:
        print('\nMagicBox: Started...')
        worms_result = magicbox.execute()
    except Exception as e:
        print('Test failed: ' + unicode(e))
        raise

    print('\n=== MagicBox: Finished. ===')
