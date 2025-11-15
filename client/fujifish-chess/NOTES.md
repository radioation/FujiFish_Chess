# curl

```bash
# get state/join
curl -X POST "http://10.25.50.61:5365/state?table=moe&player=henry" | jq
curl -X POST "http://10.25.50.61:5365/state?table=moe&player=shawn" | jq

# view
curl -X POST "http://10.25.50.61:5365/view?table=moe" | jq

# move
curl -X POST "http://10.25.50.61:5365/move?player=henry&table=moe&move=e2e4" | jq
curl -X POST "http://10.25.50.61:5365/move?player=shawn&table=moe&move=e7e5" | jq

# leave/quit
curl -X POST "http://10.25.50.61:5365/leave?table=moe&player=henry" | jq

# view tables
curl -X GET "http://10.25.50.61:5365/tables" | jq

```


