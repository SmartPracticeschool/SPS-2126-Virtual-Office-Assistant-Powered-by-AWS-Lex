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

import boto3
import pprint
client = boto3.client('lex-runtime')
print '------------------------------'
print " Starting bot "
print '------------------------------'
resp = client.post_text(botName='PollexyTestBot',
                        botAlias='Latest',
                        userId='tester',
                        inputText='I want to test Pollexy.')
done = False
while not done:

    if resp['dialogState'] == 'ReadyForFulfillment':
        done = True

    elif resp['dialogState'] == 'ElicitSlot':
        answer = raw_input(resp['message'])

    else:
        print resp['dialogState']
        print resp

    pprint.pprint(resp)
    if not done:
        emergency_resp = client.post_text(botName='PollyEmergencyBot',
                                          botAlias='LATEST',
                                          userId='tester',
                                          inputText=answer)
        print emergency_resp

        resp = client.post_text(botName='PollexyTestBot',
                                botAlias='LATEST',
                                userId='tester',
                                inputText=answer)
        print resp
