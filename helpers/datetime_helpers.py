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

def is_timezone_naive(dt):
    if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        return False
    else:
        return True


def check_if_timezone_naive(dt, name="variable"):
    if is_timezone_naive(dt):
        raise ValueError("datetime %s has no timezone" % name)
