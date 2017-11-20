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

import pygame
import speech_recognition as sr
import time


r = sr.Recognizer()


def listen():
    with sr.Microphone(sample_rate=44100) as source:
#        r.adjust_for_ambient_noice(source)
        print 'Listening . . .'
        audio = r.listen(source)
        print 'Done listening. Writing file . . . '

        with open('audio.wav', 'wb') as f:
            f.write(audio.get_wav_data())
        print 'Playing wav file . . . '
        pygame.mixer.pre_init(44100,-16,2, 2048)
        pygame.mixer.init()
        pygame.mixer.music.load('audio.wav')
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() == True:
            time.sleep(1)

if __name__ == '__main__':
    listen()
