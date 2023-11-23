## Flask Application Creation

1.No need pipenv (virtual environment)

2.Install dependecies

```
pip install -r requirements.txt
```

3.Running flask Application

```
flask run -h 0.0.0.0 -p 5000
```

## Dockerfile

1.Create Dockerfile

2.Build the image

```
docker build -t image_name .
```

3.Run the image (container creation)

```
docker run -p 5000:5000 --name container_name image_name
```

4.Tagging the image

```
docker tag image_name pr454th/image_name:version_no
```

5.Push to docker hub

```
docker push pr454th/image_name:version_no
```
