# Working with containerized Terraform

Run Docker container:
```
docker run -itd \
  --name terraform \
  --entrypoint /bin/sh \
  -w /workspace \
  -v $(pwd):/workspace \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  hashicorp/terraform:light
```

Access container:
```
docker exec -it terraform sh
```

Switch to environment directory:
```
cd aws/environments/stage
```
