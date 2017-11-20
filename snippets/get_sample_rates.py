# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not
# use this file except in compliance with the License. A copy of the
# License is located at:
#    http://aws.amazon.com/asl/
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, expressi
# or implied. See the License for the specific language governing permissions 
# and limitations under the License.

import sounddevice as sd

samplerates = 16000, 32000, 44100, 48000, 96000, 128000
device = 2

supported_samplerates = []
for fs in samplerates:
    try:
        sd.check_input_settings(device=device, samplerate=fs)
    except Exception as e:
        print(fs, e)
    else:
        supported_samplerates.append(fs)
print(supported_samplerates)
