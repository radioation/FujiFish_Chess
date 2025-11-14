
```bash
 # get state without joining
 curl -X GET "http://10.25.50.61:5364/view?player=gus&table=lounge"

 # add two players to server
 curl -X POST "http://10.25.50.61:5364/state?player=henry&table=lounge"
 curl -X POST "http://10.25.50.61:5364/state?player=shawn&table=lounge"

 # leave server
 curl -X POST "http://10.25.50.61:5364/leave?player=henry&table=lounge"

 # rejoin server
 curl -X POST "http://10.25.50.61:5364/state?player=henry&table=lounge"

 # get state without joining
 curl -X GET "http://10.25.50.61:5364/view?player=gus&table=lounge"

 # post moves 
 curl -X POST "http://10.25.50.61:5364/move?player=henry&table=lounge&move=e2e4"
 curl -X POST "http://10.25.50.61:5364/move?player=shawn&table=lounge&move=e2e4"
 curl -X POST "http://10.25.50.61:5364/move?player=henry&table=lounge&move=e2e4"
```

