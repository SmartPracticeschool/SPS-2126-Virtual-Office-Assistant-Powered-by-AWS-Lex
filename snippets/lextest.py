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

from babylex import LexSession
responses = ['nope', 'yes', "he's not here", "yea", "yep", "I am", "yes I am"]
lex_session = LexSession(bot="PollexyTestBot", alias="$LATEST", user="troy")

print('------------------------------')
print(" Starting bot ")
print('------------------------------')
resp = lex_session.text("Verify location for owen")
print(resp)
# resp = lex_session.text('yes')
# print resp
# quit()
yes_file = './yesiam.wav'
ctype = 'audio/l16; rate=16000; channels=1'
with open(yes_file) as f:
    audio = f.read()
resp = lex_session.content(ctype=ctype,
                           accept='text/plain; charset=utf-8',
                           data=audio)
# for r in responses:
#    resp = lex_session.text("Verify location for Owen")
#    resp = lex_session.text(r)
#    print "USER RESPONSE={}".format(r)
#    if resp["dialogState"] == 'Failed':
#        print 'Owen is NOT there'
#    else:
#        print 'Owen IS there'
print('------------------')

print((resp.text))
print((resp.content))
print((resp.headers))
