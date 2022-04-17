## Developer set-up


Using conda and miniforge on mac m1 else problems with scipy etc. 

```shell
conda create --name hyui python=3.10 
conda activate hyui
conda install pyscopg2 # pip fails b/c of c compiler
conda install scipy # pip fails b/c of c compiler
pip3 install -r requirements.txt
```

TODO: prepare a separate `requirements.txt` for docker

