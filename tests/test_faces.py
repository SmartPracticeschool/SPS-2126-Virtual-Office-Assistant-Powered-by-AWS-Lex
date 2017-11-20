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

from mock import patch
from moto import mock_s3
from face.face import FaceManager
import boto3
from botocore.stub import Stubber
import pytest

upload_response = """
{"FaceRecords": [{"FaceDetail": {"BoundingBox": {"Width":
0.4787878692150116, "Top": 0.1344444453716278, "Left":
0.2545454502105713, "Height": 0.2633333206176758}, "Landmarks":
[{"Y": 0.24124731123447418, "X": 0.4089203476905823, "Type":
"eyeLeft"}, {"Y": 0.25501716136932373, "X": 0.5832593441009521,
"Type": "eyeRight"}, {"Y": 0.30612853169441223, "X":
0.4805133044719696, "Type": "nose"}, {"Y": 0.3270060122013092, "X":
0.39672449231147766, "Type": "mouthLeft"}, {"Y": 0.3394944369792938,
"X": 0.562700629234314, "Type": "mouthRight"}], "Pose": {"Yaw":
-2.5392000675201416, "Roll": 7.94596529006958, "Pitch":
-8.635812759399414}, "Quality": {"Sharpness": 50.0, "Brightness":
52.51749801635742}, "Confidence": 99.99465942382812}, "Face":
{"BoundingBox": {"Width": 0.4787878692150116, "Top":
0.1344444453716278, "Left": 0.2545454502105713, "Height":
0.2633333206176758}, "FaceId":
"d5077d28-4746-577a-b03d-f736392aaa9c", "Confidence":
99.99465942382812, "ImageId":
"348dae27-fcf9-59b9-ae4c-c6d21e3b8cad"}}], "OrientationCorrection":
"ROTATE_0"}
"""


@mock_s3
@patch.object(FaceManager, 'does_bucket_exist')
def test_creating_fm_sets_bucket(exist_mock):
    exist_mock.return_value = True
    fm = FaceManager(Bucket="test")
    assert fm.bucket == "test"


@mock_s3
def test_creating_fm_with_no_bucket_throws_error():
    with pytest.raises(Exception) as exc:
        FaceManager()
    assert 'Missing parameter: Bucket' in str(exc.value)


@mock_s3
def upload_face_with_no_person_throws_error():
    with pytest.raises(Exception) as exc:
        fm = FaceManager(Bucket="test")
        fm.upload_face(Path="./file.txt", Collection="Test")
    assert 'Missing parameter: Person' in str(exc.value)


@mock_s3
def upload_face_with_no_path_throws_error():
    with pytest.raises(Exception) as exc:
        fm = FaceManager(Bucket="test")
        fm.upload_face()
    assert 'Missing parameter: Path' in str(exc.value)


@mock_s3
def upload_face_with_no_collection_throws_error():
    with pytest.raises(Exception) as exc:
        fm = FaceManager(Bucket="test")
        fm.upload_face(Path="./file.txt")
    assert 'Missing parameter: Collection' in str(exc.value)


@mock_s3
@patch("os.path.isfile")
def upload_face_with_missing_path_throws_error(isfile_mock):
    isfile_mock.return_value = False
    with pytest.raises(Exception) as exc:
        fm = FaceManager(Bucket="test")
        fm.upload_face(Path="./file.txt")
    assert 'File not found: ./file.txt' in str(exc.value)


@patch.object(FaceManager, 'does_bucket_exist')
@patch('face.face.FaceManager.error_if_file_missing')
@mock_s3
def test_reko(isfile_mock, exist_mock):
    exist_mock.return_value = True
    client = boto3.client('rekognition')
    stubber = Stubber(client)
    ep = {
        'Image': {
            'S3Object': {
                'Bucket': 'mybucket',
                'Name': 'mykey'
            }
        },
        'CollectionId': 'Test',
        'ExternalImageId': 'mykey'
    }
    stubber.add_response(method='index_faces',
                         service_response={},
                         expected_params=ep)
    stubber.activate()
    with patch.object(FaceManager, 'upload_to_s3', return_value='mykey'):
        with stubber:
            fm = FaceManager(Path="./test.txt", Bucket="mybucket")
            fm.upload_face(Path="./file.txt", Collection="Test", Person='x',
                           RekognitionStub=client)


@patch.object(FaceManager, 'does_bucket_exist')
@patch.object(FaceManager, 'get_file_data')
@mock_s3
def test_throw_error_if_bucket_does_not_exist(file_data_mock, exist_mock):
    exist_mock.return_value = True
    test_bucket = "test_data"
    file_data_mock.return_value = test_bucket
    s3 = boto3.client('s3')
    resource = boto3.resource('s3')
    s3.create_bucket(Bucket=test_bucket)
    fm = FaceManager(Bucket=test_bucket)
    fm.upload_to_s3('./test.txt', 'calvin')
    bucket = resource.Bucket(test_bucket)
    for obj_sum in bucket.objects.all():
        obj = resource.Object(obj_sum.bucket_name, obj_sum.key)
