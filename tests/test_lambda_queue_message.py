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

from lambda_functions.queue_messages import handler
from scheduler.scheduler import Scheduler
from mock import patch
from moto import mock_sqs, mock_dynamodb2
import pytest
import json


@pytest.fixture
def event():
    return json.loads("""
        {
        "message": {
            "Start": "2012-01-01 01:00:00+00:00",
            "Body":  "This is the message",
            "DeviceName": "test_device",
            "End": "2013-01-01 01:00:00+00:00",
            "Recurrence": "FREQ=DAILY"
            }
        }
    """)


@mock_dynamodb2
@mock_sqs
def test_schedulemessage_called_with_good_data(event):
    with patch.object(Scheduler, 'schedule_message', return_value=None) as m:
        handler(event, None)
    assert m.called


@mock_dynamodb2
@mock_sqs
def test_invalid_start_throws_exception(event):
    event['message']['Start'] = 'bad data'
    with patch.object(Scheduler, 'schedule_message', return_value=None):
        with pytest.raises(ValueError) as exc:
            handler(event, None)
    assert 'Invalid start date' in str(exc.value)
