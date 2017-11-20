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

import yaml
import os.path


class ConfigHelper(object):
    def __init__(self):
        config_file = '/etc/pollexy.yaml'
        if not os.path.isfile(config_file):
            self.config = None
            return

        with open(config_file, 'r') as stream:
            try:
                y = yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        self.config = y
