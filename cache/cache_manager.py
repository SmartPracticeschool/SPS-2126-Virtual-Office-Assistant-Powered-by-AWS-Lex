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
import os
import os.path
import logging


class CacheManager(object):
    def __init__(self, **kwargs):
        self.cache_root_folder = kwargs.get("cache_folder", "~/.pollexy/cache")
        self.bucket_name = kwargs.get("BucketName", "")
        self.base_folder = os.path.expanduser("~/.pollexy/.cache")
        self.cache_name = kwargs.get("CacheName", "")

        if not self.cache_name:
            raise ValueError("No cache name provided")
        self.local_cache_folder = "%s/%s" % (self.base_folder, self.cache_name)

        if not self.bucket_name:
            raise ValueError("No S3 bucket name provided")

        self.verify_cache_folder()

    def verify_cache_folder(self):
        try:
            logging.debug("Verifying that %s exists" % self.local_cache_folder)
            os.makedirs(self.local_cache_folder)
        except OSError:
            if not os.path.isdir(self.local_cache_folder):
                raise

    def sync_remote_folder(self):
        client = boto3.client('s3')
        files = self.get_remote_file_list()
        if files:
            logging.info("Syncing %s/%s" % (self.bucket_name,
                                            self.cache_name))
            for file in files:
                if file["Key"].endswith('/'):
                    continue
                local_file = "%s/%s" % (self.base_folder, file["Key"])
                logging.info(local_file)
                if not os.path.exists(local_file):
                    logging.info("...Syncing  %s" % local_file)
                    print "Syncing cache: %s" % local_file
                    client.download_file(self.bucket_name,
                                         file["Key"],
                                         local_file)
        else:
            logging.warn("No files in %s/%s" % (self.bucket_name,
                                                self.cache_name))

    def get_remote_file_list(self):
        client = boto3.client('s3')
        print("{}/{}".format(self.bucket_name, self.cache_name))
        logging.info("Syncing %s/%s" % (self.bucket_name, self.cache_name))
        objects = client.list_objects(Bucket=self.bucket_name,
                                      Prefix="%s/" % self.cache_name)
        if "Contents" not in objects.keys():
            raise StopIteration
        for result in objects["Contents"]:
            yield result

    def get_file_count(self):
        return sum(1 for _ in self.get_remote_file_list())
