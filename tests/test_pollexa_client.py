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

""" all unit tests """
import pytest
import boto3
from mock import mock_open, patch
import unittest
from moto import mock_sqs, mock_s3, mock_dynamodb2
import arrow
from messages.message_manager import MessageManager, get_queue  # noqa: E402
from cache.cache_manager import CacheManager  # noqa: E402


class TestMessageManager(unittest.TestCase):
    @mock_sqs
    @mock_sqs
    def test_can_create_missing_queue_automatically(self):
        device_name = 'ABCDEFG'
        queue = get_queue(device_name)
        self.assertIsNone(queue)

        message_manager_under_test = MessageManager(DeviceName=device_name)
        self.assertIsNotNone(message_manager_under_test.queue)

    @mock_sqs
    def test_throw_value_error_on_missing_device_name(self):
        with self.assertRaises(Exception) as context:
            MessageManager()
        print((context.exception))
        self.assertTrue('Missing device name' in context.exception)

    @mock_sqs
    @mock_dynamodb2
    def test_can_read_one_message_from_queue(self):
        message_manager_under_test = MessageManager(DeviceName="TEST")
        message_manager_under_test.publish_message(
                UUID="test",
                ExpirationDateTimeInUtc="2013-01-01 11:00",
                Body="Hey there")
        message_manager_under_test.get_messages()
        self.assertEqual(1, len(message_manager_under_test.messages))

    @mock_dynamodb2
    @mock_sqs
    def test_can_read_more_than_one_message_from_queue(self):
        message_manager_under_test = MessageManager(DeviceName="TEST")
        message_manager_under_test.publish_message(
                UUID="test",
                ExpirationDateTimeInUtc="2013-01-01 11:00",
                Body="Hey there")
        message_manager_under_test.publish_message(
                UUID="test",
                ExpirationDateTimeInUtc="2013-01-01 11:00",
                Body="Hey there")
        message_manager_under_test.publish_message(
                UUID="test",
                ExpirationDateTimeInUtc="2013-01-01 11:00",
                Body="Hey there")
        message_manager_under_test.get_messages()
        self.assertEqual(3, len(message_manager_under_test.messages))

    @mock_sqs
    @mock_dynamodb2
    def test_can_prevent_deletion_of_message(self):
        message1 = "Hey there 1"
        message2 = "Hey there 2"
        final_speech = "<speak><p>Hey there 1</p><p>Hey there 2</p></speak>"
        message_manager_under_test = MessageManager(DeviceName="TEST")
        message_manager_under_test.publish_message(
                UUID="test",
                ExpirationDateTimeInUtc="2018-01-01 11:00",
                Body=message1)
        message_manager_under_test.publish_message(
                UUID="test",
                ExpirationDateTimeInUtc="2018-01-01 11:00",
                Body=message2)
        self.assertEqual(message_manager_under_test.write_speech(True),
                         final_speech)
        self.assertEqual(message_manager_under_test.write_speech(False),
                         final_speech)

    @mock_sqs
    @mock_dynamodb2
    def test_can_properly_write_speech(self):
        message1 = "Hey there 1"
        message2 = "Hey there 2"
        final_speech = "<speak><p>Hey there 1</p><p>Hey there 2</p></speak>"
        message_manager_under_test = MessageManager(DeviceName="TEST")
        message_manager_under_test.publish_message(
                UUID="test",
                ExpirationDateTimeInUtc="2018-01-01 11:00",
                Body=message1)
        message_manager_under_test.publish_message(
                UUID="test",
                ExpirationDateTimeInUtc="2018-01-01 11:00",
                Body=message2)
        self.assertEqual(message_manager_under_test.write_speech(),
                         final_speech)

    @mock_sqs
    def test_empty_body_throws_value_error(self):
        with self.assertRaises(Exception) as context:
            message_manager_under_test = MessageManager(DeviceName="TEST")
            message_manager_under_test.publish_message(UUID='test')
        self.assertTrue('No message body provided' in context.exception)

    @mock_sqs
    def test_empty_uuid_throws_value_error(self):
        with self.assertRaises(Exception) as context:
            message_manager_under_test = MessageManager(DeviceName="TEST")
            message_manager_under_test.publish_message(
                Body="Test")
        self.assertTrue('No uuid provided' in context.exception)

    @mock_sqs
    @mock_dynamodb2
    def test_can_publish_message_with_expiration(self):
        body = 'hey there'
        expire_datetime_in_utc = '2016-12-31 01:00 UTC'
        message_manager_under_test = MessageManager(DeviceName="TEST")
        message_manager_under_test.publish_message(
                UUID='test',
                ExpirationDateTimeInUtc=expire_datetime_in_utc,
                Body=body)
        message_manager_under_test.get_messages()
        polexa_message_under_test = message_manager_under_test.messages[0]
        self.assertEqual(
                arrow.get(expire_datetime_in_utc),
                polexa_message_under_test.expiration_datetime_in_utc)

    @mock_sqs
    @mock_dynamodb2
    def test_can_publish_message_with_body(self):
        body = 'hey there'
        message_manager_under_test = MessageManager(DeviceName="TEST")
        message_manager_under_test.publish_message(
                UUID="test_uuid",
                ExpirationDateTimeInUtc="2013-01-01 11:00",
                Body=body)
        message_manager_under_test.get_messages()
        polexa_message_under_test = message_manager_under_test.messages[0]
        self.assertEqual(body, polexa_message_under_test.body)

    @mock_sqs
    @mock_dynamodb2
    def test_can_publish_message_with_uuid(self):
        body = 'hey there'
        message_manager_under_test = MessageManager(DeviceName="TEST")
        message_manager_under_test.publish_message(
                UUID="test_uuid",
                ExpirationDateTimeInUtc="2013-01-01 11:00",
                Body=body)
        message_manager_under_test.get_messages()
        polexa_message_under_test = message_manager_under_test.messages[0]
        assert polexa_message_under_test.uuid_key == "test_uuid"

    @mock_sqs
    @mock_dynamodb2
    def test_can_parse_valid_expiration_timestamp(self):
        message_manager_under_test = MessageManager(DeviceName="TEST")
        message_manager_under_test.publish_message(
                UUID="test",
                ExpirationDateTimeInUtc="2013-01-01 11:00",
                Body="Hey there")
        message_manager_under_test.get_messages()
        polexa_message_under_test = message_manager_under_test.messages[0]
        self.assertEqual(
                polexa_message_under_test.expiration_datetime_in_utc.year,
                2013)
        self.assertEqual(
                polexa_message_under_test.expiration_datetime_in_utc.hour,
                11)

    @mock_sqs
    @mock_dynamodb2
    def test_expired_message_is_expired(self):
        message_manager_under_test = MessageManager(DeviceName="TEST")
        expiration_date = arrow.utcnow().replace(days=-7)
        message_manager_under_test.publish_message(
                UUID='test',
                ExpirationDateTimeInUtc=expiration_date.isoformat(),
                Body="Hey there")
        message_manager_under_test.get_messages()
        polexa_message_under_test = message_manager_under_test.messages[0]
        self.assertTrue(polexa_message_under_test.is_expired)


@mock_s3
def test_missing_cache_name_throws_error():
    with pytest.raises(ValueError) as exception:
        CacheManager(BucketName="Test")

    assert 'No cache name provided' in str(exception.value)


@mock_s3
def test_missing_bucket_name_throws_error():
    with pytest.raises(ValueError) as exception:
        CacheManager(CacheName="test")

    assert 'No S3 bucket name provided' in str(exception.value)


@mock_s3
def test_empty_bucket_name_throws_error():
    with pytest.raises(ValueError) as exception:
        CacheManager(BucketName="", CacheName="test")

    assert 'No S3 bucket name provided' in str(exception.value)


@mock_s3
def test_can_pull_down_cache_folder():
    s3 = boto3.resource('s3')
    s3.create_bucket(Bucket="test-bucket")
    with patch('__builtin__.open', mock_open(read_data="TestData"),
               create=True) as m:
        with open('file') as h:
            s3.Bucket('test-bucket').put_object(Key='chimes/file1', Body=h)
            s3.Bucket('test-bucket').put_object(Key='chimes/file2', Body=h)
            s3.Bucket('test-bucket').put_object(Key='chimes/file3', Body=h)
    cache_manager = CacheManager(BucketName="test-bucket", CacheName="chimes")
    with patch.object(boto3.s3.transfer.S3Transfer,
                      "download_file",
                      return_value=None) as m:
        cache_manager.sync_remote_folder()
    assert len(m.mock_calls) == 3


if __name__ == '__main__':
        unittest.main()
