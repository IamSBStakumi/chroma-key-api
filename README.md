# Chroma-key-API

![Python](https://img.shields.io/badge/-Python-F2C63C.svg?logo=python&style=for-the-badge)
![poetry](https://img.shields.io/badge/-poetry-000099.svg?logo=poetry&style=for-the-badge)
![fastAPI](https://img.shields.io/badge/-fastAPI-003333.svg?logo=fastAPI&style=for-the-badge)
![OpenCV](https://img.shields.io/badge/-OpenCV-5C3EE8.svg?logo=OpenCV&style=for-the-badge)
![numpy](https://img.shields.io/badge/-numpy-013243.svg?logo=numpy&style=for-the-badge)

## ローカルで実行

ルートフォルダ上で Docker を起動する

```bash
docker build -t api:v1 .
```

docker run 実行

```bash
docker run -it -p 8080:8080 api:v1
```
