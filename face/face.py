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
import os.path
import uuid
from botocore.client import ClientError


def error_if_missing(kwargs, params):
    for param in params:
        if param not in kwargs:
            raise TypeError('Missing parameter: %s' % param)


class FaceManager(object):
    def __init__(self, **kwargs):
        error_if_missing(kwargs, ['Bucket'])
        self.bucket = kwargs.get('Bucket', '')
        if not self.does_bucket_exist(self.bucket):
            raise ValueError("Bucket does not exist: %s" % self.bucket)

    def error_if_file_missing(self, path):
        if not os.path.isfile(path):
            raise OSError("File not found: %s" % path)

    def does_bucket_exist(self, bucket):
        try:
            s3 = boto3.resource('s3')
            s3.meta.client.head_bucket(Bucket=bucket)
            return True
        except ClientError as exc:
            print str(exc)
            return False

    def get_file_data(self, path):
        return open(path, 'rb')

    def upload_to_s3(self, path, person):
        client = boto3.client('s3')
        filename = os.path.basename(path)
        id = uuid.uuid4()
        key = '%s-%s' % (id, filename)
        data = self.get_file_data(path)
        client.put_object(
            Bucket=self.bucket,
            Key=key, Body=data
        )
        client.put_object_tagging(
            Key=key,
            Bucket=self.bucket,
            Tagging={
                'TagSet': [
                    {
                        'Key': 'person',
                        'Value': person
                    }
                ]
            }
        )
        return key

    def match_face(self, **kwargs):
        error_if_missing(kwargs, ['Path', 'Collection'])
        collection = kwargs.get("Collection", "")
        path = kwargs.get("Path", "")
        reko = boto3.client('rekognition')
        with open(path, 'rb') as image:
            response = reko.search_faces_by_image(
                CollectionId=collection,
                Image={
                    'Bytes': image.read()
                }
            )
        print response

    def upload_face(self, **kwargs):
        error_if_missing(kwargs, ['Path', 'Collection', 'Person'])
        if 'RekognitionStub' in kwargs:
            reko = kwargs.get('RekognitionStub')
            print "Faking out a Rekognition"
        else:
            reko = boto3.client('rekognition')

        person = kwargs.get("Person")
        collection = kwargs.get("Collection", "")
        path = kwargs.get("Path", "")
        self.error_if_file_missing(path)
        key = self.upload_to_s3(path, person)
        response = reko.index_faces(
                Image={
                        'S3Object': {
                            'Bucket': self.bucket,
                            'Name': key
                        }
                      },
                CollectionId=collection,
                ExternalImageId=key
        )
        return response
