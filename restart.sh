
#!/bin/sh

# Test by running `heroku run "~/restart.sh"`

curl -X DELETE "https://api.heroku.com/apps/${HEROKU_APP_NAME}/dynos" \
  --user "${HEROKU_CLI_USER}:${HEROKU_CLI_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/vnd.heroku+json; version=3"
