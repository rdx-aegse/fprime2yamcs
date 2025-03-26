"""
Created on Mon Feb 3 2025

Main script for the "YAMCS mission databases for Fprime" generator.

This script generates YAMCS mission database files based on Fprime artifacts.
It requires:
- A directory containing `TopologyDictionary.json` and `Packets.xml` files.
- An output directory for the generated YAMCS MDB files.
- An optional MDB version.

@author: GregoireMarchetaux
"""

import os
import argparse
from fprime_parser import DeploymentDictLoader, PacketsListLoader
from yamcs_mdb_generator.yamcs_mdb_gen import YAMCSMDBGen
from typing import Dict, Any

# --- Helper Functions -----------------------------------------------------------------------------------------

def read_inputs(artifacts_dir: str, topology_dir:str) -> (str, str, str):
    """
    Validates that the given directory contains required files and extracts the deployment name.
    
    Parameters:
    artifacts_dir (str): Path to the fprime artifacts directory.
    topology_dir (str): Path to the fprime topology directory
    
    Returns:
    Tuple[str, str, str]: Paths to TopologyDictionary.json and Packets.xml, and extracted deployment name. None otherwise
    
    Raises:
    FileNotFound if either topology or packets are not found
    ValueError (if topology and packets file don't have the same base name)
    """
    topology_dict_file = None
    packets_file = None
    depl_name = None

    # Check for required files in the directories
    for file_name in os.listdir(artifacts_dir):
        if file_name.endswith("TopologyDictionary.json"):
            topology_dict_file = os.path.join(artifacts_dir, file_name)
            depl_name_top = file_name.split("TopologyDictionary.json")[0]
            
    for file_name in os.listdir(topology_dir):
        if file_name.endswith("Packets.xml"):
            packets_file = os.path.join(topology_dir, file_name)
            depl_name_pckts = file_name.split("Packets.xml")[0]

    if not topology_dict_file or not packets_file:
        raise FileNotFoundError(
            f"The directories '{artifacts_dir}' must contain both 'TopologyDictionary.json' and 'Packets.xml' files."
        )
        
    if depl_name_top != depl_name_pckts:
        raise ValueError(f'{topology_dict_file} and {packets_file} should have the same base name (application name)')
    
    return topology_dict_file, packets_file, depl_name_top

def type_contains_array(type_name: str, types_decl: Dict[str, Any]) -> bool:
    """
    Determines if a type contains an array at any level of its structure.
    
    Parameters:
    type_name (str): Name of the type to analyze.
    types_decl (Dict[str, Any]): Dictionary of type declarations parsed from Fprime dictionary.
    
    Returns:
    bool: True if the type contains an array; False otherwise.
    """
    #temp
    print(f'Processing type_name {type_name}')
    
    #Arrays have to be in type declarations
    if type_name in types_decl:
        type_info = types_decl[type_name]
        
        if type_info["kind"] == "array":
            return True  # Base case: if the type is an array, return True

        if type_info["kind"] == "struct":
            # Recursively check each member of the struct
            return any(type_contains_array(member_type, types_decl) for member_type in type_info["members"].values())

    # For native types and enums as well as types not in the dictionary, return False
    return False

def parse_args():
    '''
    Set up argparse for the script
    '''    
    parser = argparse.ArgumentParser(
        description="Generate YAMCS mission database files based on Fprime artifacts."
    )
    
    parser.add_argument(
        "--fprime-artifacts",
        required=True,
        help="Path to the fprime deployment artifacts directory containing [appName]TopologyDictionary.json."
    )
    
    parser.add_argument(
        "--fprime-topology",
        required=True,
        help="Path to the fprime deployment topology directory containing [appName]Packets.xml."
    )
    
    parser.add_argument(
        "--yamcs-mdb",
        required=True,
        help="Path to the YAMCS mission database directory where the output files will be saved."
    )
    
    parser.add_argument(
        "--mdb-version",
        default="1.0",
        help="Version to show in the mission database (default: 1.0)."
    )
    
    return parser.parse_args()

def remove_prefix_from_dict(d, prefix):
    """
    Removes a specified prefix from all keys and values in a dictionary, recursively.

    Parameters:
    - d (dict): The dictionary whose keys and values should be processed.
    - prefix (str): The prefix to remove from the dictionary keys and values.

    Returns:
    - dict: A new dictionary with the prefix removed from keys and values.
    """
    # Create a new dictionary with modified keys and values
    new_dict = {}
    
    for key, value in d.items():
        # Use removeprefix to remove the prefix from the key
        new_key = key.removeprefix(prefix)
        
        # Process the value (whether it's a string, dict, or list)
        new_value = remove_prefix_from_value(value, prefix)
        
        new_dict[new_key] = new_value
    
    return new_dict

def remove_prefix_from_list(lst, prefix):
    """
    Removes a specified prefix from all elements in a list, recursively.

    Parameters:
    - lst (list): The list whose elements should be processed.
    - prefix (str): The prefix to remove from the list elements.

    Returns:
    - list: A new list with the prefix removed from string elements.
    """
    # Process each item in the list
    return [remove_prefix_from_value(item, prefix) for item in lst]

def remove_prefix_from_value(value, prefix):
    """
    Removes the specified prefix from a given value. Handles strings, dictionaries, and lists.

    Parameters:
    - value (any): The value to process. Can be a string, dictionary, or list.
    - prefix (str): The prefix to remove from the value.

    Returns:
    - The modified value with the prefix removed (if applicable).
    """
    # If the value is a dictionary, process it recursively
    if isinstance(value, dict):
        return remove_prefix_from_dict(value, prefix)
    
    # If the value is a list, process it recursively
    elif isinstance(value, list):
        return remove_prefix_from_list(value, prefix)
    
    # If the value is a string, remove the prefix
    elif isinstance(value, str):
        return value.removeprefix(prefix)
    
    # Otherwise, leave the value unchanged (e.g., numbers, booleans, etc.)
    else:
        return value

# --- Main Script ---------------------------------------------------------------------------------------------

if __name__ == "__main__":
    args = parse_args()

    fprime_artifacts_dir = args.fprime_artifacts
    fprime_topology_dir = args.fprime_topology
    output_dir = args.yamcs_mdb
    mdb_version = args.mdb_version

    try:
        topology_dict_path, packets_xml_path, depl_name = read_inputs(fprime_artifacts_dir, fprime_topology_dir)
        print(f"Successfully read from fprime artifacts directory for Fprime application: {depl_name}")
    except Exception as e:
        print(e)
        sys.exit(1)

    # Parse F' deployment dictionary
    dict_loader = DeploymentDictLoader(topology_dict_path)
    types_decl, channels_types, commands = dict_loader.parse()
    
    #channels types and commands have depl. prepended to their keys where depl is the deployment name; whereas the others don't. So strip it. 
    channels_types = remove_prefix_from_dict(channels_types, depl_name+'.')
    commands = remove_prefix_from_dict(commands, depl_name+'.')
    
    #temp
    print('-----------types_decl-------------')
    print(types_decl)
    print('-----------channels_types--------------')
    print(channels_types)
    print('-------------commands-----------------')
    print(commands)

    # Parse packets XML
    packets_loader = PacketsListLoader(packets_xml_path)
    packets = packets_loader.get_packets()
    
    #temp
    print('-----------packets-------------')
    print(packets)

    # Create YAMCS MDB generator
    yamcs_gen = YAMCSMDBGen(depl_name, mdb_version, output_dir)

    array_sizes = {}  # Memorize array sizes when processing types

    # Convert and add types; arrays and aggregates go last because they need basic types to be defined
    for type_name, type_info in types_decl.items():
        if type_info["kind"] == "enum":
            yamcs_gen.addEnumType(type_name, type_info["representationtype"], type_info["values"])
        elif type_info["kind"] == "native":
            yamcs_gen.addPrimitiveType(type_name)
    
    for type_name, type_info in types_decl.items():
        if type_info["kind"] == "struct":
            yamcs_gen.addAggregateType(type_name, type_info["members"])
        elif type_info["kind"] == "array":
            yamcs_gen.addArrayType(type_name, type_info["elementType"])
            array_sizes[type_name] = type_info["size"]

    # Add telemetry packets one by one from the list in the XML
    for packet_id, packet_info in packets.items():
        tm_packet = YAMCSMDBGen.TMPacket(packet_info["name"], packet_id)

        for channel_name in packet_info["channels"]:
            channel_type = channels_types.get(channel_name)
            if channel_type in array_sizes:
                tm_packet.addArray(channel_name, channel_type, array_sizes[channel_type])
            else:
                tm_packet.addParam(channel_name, channel_type)

        yamcs_gen.addTMTC(tm_packet)

    # Add commands one at a time
    for cmd_name, cmd_info in commands.items():
        command = YAMCSMDBGen.Command(cmd_name, cmd_info["opcode"])
        contains_array_arg = False

        for arg in cmd_info["args"]:
            for arg_name, arg_type in arg.items():
                if type_contains_array(arg_type, types_decl):
                    contains_array_arg = True
                    print(
                        f"Detected that type {arg_type} contains one or more array types. "
                    )
                    break
                command.addParam(arg_name, arg_type)

            if contains_array_arg:
                break

        if not contains_array_arg:
            yamcs_gen.addTMTC(command)
        else:
            print(f"=> Ignoring command '{command.name}' due to unsupported array arguments.")

    # Done building. Generate YAMCS MDB CSV files
    yamcs_gen.generateCSVs()

    print(f"YAMCS mission database worksheets saved in {output_dir} with prefix '{depl_name}'")
