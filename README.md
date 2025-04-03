# fprime2yamcs

YAMCS mission database generator for Fprime applications, in order to interact with an Fprime deployment like GDS but with YAMCS. 

## Requirements

Fprime requirements:
- 3.6.2 (untested above, especially if [supporting fpp packet sets](https://github.com/rdx-aegse/fprime2yamcs/issues/2) is still open)
- Already use or accept the use of TlmPacketizer instead of TlmChan for the TM packetizer
- Currently, only text events (as opposed to encoded as LogBuffers like ActiveLogger does) are supported. The necessary ActiveLogger replacement, TextEventPacketizer, is provided in our fprime fork.

## Usage

Shown in [integration demonstration](https://github.com/rdx-aegse/yamcs_system_demo), but the general plan is as follows:

1. Use [RDX's fprime fork](https://github.com/rdx-aegse/fprime) (currently on add_support_yamcs branch) OR equivalently:
    1. Configure Fprime for identical types of packets between TM and events. As of Fprime v3.6.2 this means changing FwTlmPacketizeIdType from U16 to U32 in config/FpConfig.h
    2. Copy over RDX's TextEventPacketizer component found in [yamcs_system_demo](https://github.com/rdx-aegse/yamcs_system_demo)/fprime_demo/src/fprime_app/fprime/Svc/TextEventPacketizer
    3. Replace ActiveLogger with TextEventPacketizer in your deployment topology (both instances.fpp and topology.fpp). This requires connecting LogText ports instead of Log ports. 
2. Call main.py pointing to your build artifacts to generate the YAMCS mission database CSVs
3. Convert the CSVs to a single XLS that YAMCS expects
4. Set up your YAMCS instance (in your maven project's src/main/yamcs/etc/ folder)
    1. to use the compatible event decoding service
    2. to use the fprime packet preprocessor
    3. to use the fprime command postprocessor
    4. to load the generated XLS
    5. to set up the TM and TC streams based on the mission database's name and abstract packet name
   Network, Docker, general YAMCS and Fprime setup & bring-up is not within scope. 
6. Do not forget to update your packet list when the telemetry changes ({deployment}Packets.xml in v3.6.2). fpp-util will say if telemetry channels are not accounted for. 



