# Deployment

## Quick start

From the commandline of the GAE

```sh
git clone https://github.com/HYLODE/HyUi.git
cd HyUi
cp .env.example .env
# Now hand edit the .env file with usernames/passwords
# Set ENV=prod (rather than dev)
pytest # OPTIONAL
docker-compose up -d --build && docker-composes logs -f
```

Go to [http://my-host-name:8094/docs](http://my-host-name:8094/docs) for the API

Go to [http://my-host-name:8095](http://my-host-name:8095) for the dashboard landing page
