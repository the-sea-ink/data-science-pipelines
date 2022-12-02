# DBPRO.IMPRO.SS22-parsing-ds-source-code

To begin with (assuming Python is set), [install NVM](https://github.com/nvm-sh/nvm#installing-and-updating) to get npm, node.js, etc. Then,
```
python -m pip install -r requirements.txt
```
Switch to virtual environment and install Regraph by executing 
```
python setup.py install
```
inside the third_library/Regraph folder.

To start a test server
```
uvicorn main:app --reload
```

To compile a frontend, `npm install` once from the project folder, then
```
npm run build
```
