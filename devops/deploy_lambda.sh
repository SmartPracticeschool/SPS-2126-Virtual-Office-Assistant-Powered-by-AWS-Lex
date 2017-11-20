FOLDER=/tmp/pollexy_queue_deploy
rm -fr $FOLDER
mkdir -p $FOLDER
cp ./lambda_functions/schedule_message.py $FOLDER
cp ./lambda_functions/queue_messages.py $FOLDER
cp ./lambda_functions/queue_immediate.py $FOLDER
cp ./lambda_functions/update_person.py $FOLDER
cp -r ./scheduler $FOLDER
cp -r ./person $FOLDER
cp -r ./helpers $FOLDER
cp -r ./locator $FOLDER
cp -r ./messages $FOLDER
cp -r ./time_window $FOLDER
cp ./sam/queue.yml $FOLDER
cp ./requirements.txt $FOLDER
touch $FOLDER/__init__.py
cd $FOLDER
virtualenv venv
. ./venv/bin/activate
pip install -r requirements.txt
deactivate
mv venv/lib/python2.7/site-packages/* .
aws cloudformation package --template-file ./queue.yml --output-template-file output.yml --s3-bucket lambda-deploys-1 --s3-prefix pollexy-queue
aws cloudformation deploy --capabilities CAPABILITY_IAM --template-file ./output.yml --stack-name pollexy-queue

