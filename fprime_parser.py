"""
Created on Mon Feb  3 2025

Fprime side for the "YAMCS mission databases for Fprime" generator. 

@author: GregoireMarchetaux
"""
#--- Imports  ------------------------------------------------------------------------------

import json
from typing import Dict, Any, List, Tuple
import xml.etree.ElementTree as ET

#--- Object definitions ---------------------------------------------------------------------

#TODO: Fork fprime_gds and modify it to get the outputs we want here instead of reinventing the wheel

class DeploymentDictLoader:
    """
    A class for loading and parsing Fprime deployment dictionary data from a JSON file.

    This class handles the extraction and formatting of type declarations,
    channel types, and commands from a structured JSON deployment dictionary.
    """

    def __init__(self, json_path: str):
        """
        Initialize the DeploymentDictLoader with the path to the JSON file.

        Args:
            json_path (str): The file path to the JSON deployment dictionary.
        """
        self.stringTypes = set()
        self.json_path = json_path
        with open(self.json_path, 'r') as f:
            self.data = json.load(f)      
            
    #--- Private methods ---------------------------------------------------------------------
            
    def _format_type_name(self, type_info: Any) -> str:
        """
        Format the type name based on the type information.

        For string types, creates a unique identifier. For other types,
        returns the name as is.

        Args:
            type_info (Any): Type information dictionary.

        Returns:
            str: Formatted type name.
        """
        if type_info['kind'] == 'string':
            stringType = f"{type_info['name']}{type_info['size']}" #Embed length information in the string type name
            self.stringTypes.add(stringType)
            return stringType
        else:
            return type_info['name'] 

    def _get_types_decl(self) -> Dict[str, Any]:
        """
        Extract and process type declarations from the JSON data.

        Returns:
            Dict[str, Any]: Processed type declarations.
        """
        raw_definitions = {t['qualifiedName']: t for t in self.data['typeDefinitions']}
        processed_types = {}

        for type_name, type_info in raw_definitions.items():
            if type_info['kind'] == 'struct':
                processed_types[type_name] = {
                    'kind': 'struct',
                    'members': {name: self._format_type_name(typeInfo['type']) 
                                for name, typeInfo in type_info['members'].items()}
                }
            elif type_info['kind'] == 'array':
                processed_types[type_name] =  {
                    'kind': 'array',
                    'size': type_info['size'],
                    'elementType': self._format_type_name(type_info['elementType'])
                }
            elif type_info['kind'] == 'enum':
                processed_types[type_name] =  {
                    'kind': 'enum',
                    'representationtype': self._format_type_name(type_info['representationType']),
                    'values': {const['name']: const['value'] for const in type_info['enumeratedConstants']}
                }
            else:
                processed_types[type_name] = {'kind': 'native'}
                
        return processed_types
            
    def _get_channel_types(self) -> Dict[str, Any]:
        """
        Extract and process channel types from the JSON data.

        Returns:
            Dict[str, Any]: Processed channel types.
        """
        return {channel['name']: self._format_type_name(channel['type']) 
                for channel in self.data['telemetryChannels']}
    
    def _get_commands(self) -> Dict[str, Any]:
        """
        Extract and process commands from the JSON data.

        Returns:
            Dict[str, Any]: Processed commands.
        """
        commands = {}
        for command in self.data['commands']:
            command_name = command['name']
            commands[command_name] = {
                "opcode": command['opcode'],
                "args": []
            }
            if 'formalParams' in command:
                for param in command['formalParams']:
                    param_type = self._format_type_name(param['type'])
                    commands[command_name]["args"].append({param['name']: param_type})
        return commands
    
    #--- Public methods ---------------------------------------------------------------------
    
    def parse(self) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Parse the deployment dictionary data.
        
        Use the channelsTypes to know for a given channel what type it has, then the 
        types declaration dictionary to know everything there is to know about that type.
        Commands also include types of arguments that can be looked up in the typesDecl dict. 

        Returns:
            Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]: 
                A tuple containing type declarations, channel types, and commands.
        """
        typesDecl = self._get_types_decl()
        channelsTypes = self._get_channel_types() 
        commands = self._get_commands()
        for s in self.stringTypes: #Add all strings encountered to the types declarations as native types
            typesDecl[s] = {'kind': 'native'}
        return typesDecl, channelsTypes, commands
#End of DeploymentDictLoader

class PacketsListLoader:
    """
    A class for loading packet definitions from an XML file.
    """

    def __init__(self, xml_path: str):
        """
        Initialize the PacketsListLoader with the path to the XML file.

        Args:
            xml_path (str): The file path to the XML packet definitions.
        """
        self.xml_path = xml_path

    def get_packets(self) -> Dict[int, Dict[str, Any]]:
        """
        Parse the XML file and extract channels lists

        Returns:
            Dict[int, Dict[str, Any]]: A dictionary of packet IDs mapped to their details (mostly channels list)
        """
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        return {
            int(packet.get('id')): {
                "name": packet.get('name'),
                "channels": [t.get('name') for t in packet.findall('channel')]
            }
            for packet in root.findall('packet')
        }
#End of PacketsListLoader

#--- Testing --------------------------------------------------------------------------------------------------
    
if __name__ == '__main__':
    # Demonstrate usage of DeploymentDictLoader
    deployment_loader = DeploymentDictLoader('dict.json')
    typesDecl, channels, commands = deployment_loader.parse()
    print('----CHANNELS----')
    print(json.dumps(channels, indent=4))
    print('----COMMANDS----')
    print(json.dumps(commands, indent=4))
    print('----TYPES----')
    print(json.dumps(typesDecl, indent=4))
    
    # Demonstrate usage of PacketsListLoader
    packets_loader = PacketsListLoader('RefPackets.xml')
    print('----PACKETS----')
    print(json.dumps(packets_loader.get_packets(), indent=4))
