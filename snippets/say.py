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

from speaker.speaker import Speaker
import boto3
import arrow

client = boto3.client('polly')
response = client.describe_voices(LanguageCode='en-AU')
d = arrow.utcnow().format('dddd, MMMM DD, YYYY')
s = Speaker(NoAudio=False)
voice_id='Joanna'
# for voice in response["Voices"]:
#    voice_id = voice["Id"]
#    print voice_id + " . . ."
s.just_say(Message="Calvin. Miss Kelly is outside your bedroom. Open your " +
           " bedroom door. Open your bedroom door and give her a hug.",
           VoiceId=voice_id,
           IncludeChime=True)
s.cleanup()
