sudo apt-get install zip unzip python3 pip -y

wget https://github.com/Kontinuum-Investment-Holdings/KIH_API/archive/refs/heads/main.zip
unzip main.zip -d .
pip3 install -r requirements.txt -t .
pip3 install -r KIH_API-main/requirements.txt -t .
mv KIH_API-main/* .

rm -rf pandas*
rm -rf numpy*
rm -rf pytz*

wget https://files.pythonhosted.org/packages/32/82/0a28e3a04411a1a4c1d099bb94349f97050579f90a0290432f09d9a58148/numpy-1.22.4-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
wget https://files.pythonhosted.org/packages/35/ad/616c27cade647c2a1513343c72c095146cf3e7a72ace6582574a334fb525/pandas-1.4.2-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
wget https://files.pythonhosted.org/packages/60/2e/dec1cc18c51b8df33c7c4d0a321b084cf38e1733b98f9d15018880fb4970/pytz-2022.1-py2.py3-none-any.whl
unzip numpy-1.22.4-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl -d . && rm -rf numpy-1.22.4-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
unzip pandas-1.4.2-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl -d . && rm -rf pandas-1.4.2-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
unzip pytz-2022.1-py2.py3-none-any.whl -d . && rm -rf pytz-2022.1-py2.py3-none-any.whl

rm main.zip
rm -rf KIH_API-main
rm requirements.txt && rm -rf .github && rm mypy.ini && rm -rf __pycache__ && rm -rf .git
rm *.bash && rm -rf *.ssh && rm -rf *.cache
zip -r code.zip .

for function in $LAMBDA_FUNCTION_NAMES
do
  mv code.zip $function.zip
  aws s3 cp $function.zip s3://kih-github/code/
  aws lambda update-function-code --function-name $function --s3-bucket kih-github --s3-key code/$function.zip
  mv $function.zip code.zip
done

exit