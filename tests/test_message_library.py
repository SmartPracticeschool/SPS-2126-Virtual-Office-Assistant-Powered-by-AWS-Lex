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

from messages.message_manager import LibraryManager
from moto import mock_dynamodb2
from mock import patch


@mock_dynamodb2
@patch('messages.message_manager.LibraryManager.create_message_library_table')
def test_table_is_created_if_does_not_exist(c_mock):
    lm = LibraryManager()
    assert lm
    assert c_mock.call_count == 1


@mock_dynamodb2
def test_can_add_message():
    lm = LibraryManager()
    lm.update_message(Name='test', Message='Full message')
    m = lm.get_message(Name='test')
    assert m['message'] == 'Full message'


@mock_dynamodb2
def test_can_update_message():
    lm = LibraryManager()
    lm.update_message(Name='test', Message='Full message')
    m = lm.get_message(Name='test')
    assert m['message'] == 'Full message'
    lm.update_message(Name='test', Message='Updated message')
    m = lm.get_message(Name='test')
    assert m['message'] == 'Updated message'


@mock_dynamodb2
def test_can_delete_message():
    lm = LibraryManager()
    lm.update_message(Name='test', Message='Full message')
    m = lm.get_message(Name='test')
    assert m['message'] == 'Full message'
    lm.delete_message(Name='test')
    m = lm.get_message(Name='test')
    assert m is None
