github link: https://github.com/wanda-26/dass-assignment2

google drive link: https://drive.google.com/file/d/1x24GNWY7gbLS7qZDgFcTXncFdFDh7ed4/view?usp=sharing


how to run:

part 1:
pylint code/
python3 -m unittest tests.test_moneypoly -v
part 2:
pytest tests/test_integration.py -v
part 3:
first put quickcart_image_x86.tar in the folder then do:
docker load -i quickcart_image_x86.tar
docker run -p 8080:8080 quickcart
pytest test_quickcart.py -v