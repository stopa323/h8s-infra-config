LAMBDA_NAME="bob-consume-view"

pip install --target ./package -r reqs.txt
cd ./package

zip -r9 ${OLDPWD}/function.zip .
cd $OLDPWD
zip -u function.zip main.py

aws lambda update-function-code --function-name $LAMBDA_NAME --zip-file fileb://function.zip

rm -f function.zip
rm -rf package/